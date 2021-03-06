import pytest
from aiohttp import web
from marshmallow import Schema, fields

from aiohttp_apispec import AiohttpApiSpec, use_kwargs, aiohttp_apispec_middleware, docs


def pytest_report_header(config):
    return """
          .   .  .                                   
,-. . ,-. |-. |- |- ,-.    ,-. ,-. . ,-. ,-. ,-. ,-. 
,-| | | | | | |  |  | | -- ,-| | | | `-. | | |-' |   
`-^ ' `-' ' ' `' `' |-'    `-^ |-' ' `-' |-' `-' `-' 
                    |          |         |           
                    '          '         '           
    """


@pytest.fixture
def request_schema():
    class RequestSchema(Schema):
        id = fields.Int()
        name = fields.Str(description='name')
        bool_field = fields.Bool()
        list_field = fields.List(fields.Int())

    return RequestSchema(strict=True)


@pytest.fixture
def request_callable_schema():
    class RequestSchema(Schema):
        id = fields.Int()
        name = fields.Str(description='name')
        bool_field = fields.Bool()
        list_field = fields.List(fields.Int())

    return RequestSchema


@pytest.fixture
def response_schema():
    class ResponseSchema(Schema):
        msg = fields.Str()
        data = fields.Dict()

    return ResponseSchema


@pytest.fixture(params=[
    ({'locations': ['query']}, True),
    ({'location': 'query'}, True),
    ({'locations': ['query']}, False),
    ({'location': 'query'}, False),
])
def aiohttp_app(
    request_schema, request_callable_schema, loop, test_client, request
):
    locations, nested = request.param

    @docs(
        tags=['mytag'],
        summary='Test method summary',
        description='Test method description',
    )
    @use_kwargs(request_schema, **locations)
    def handler_get(request):
        print(request.data)
        return web.json_response({'msg': 'done', 'data': {}})

    @use_kwargs(request_schema)
    def handler_post(request):
        print(request.data)
        return web.json_response({'msg': 'done', 'data': {}})

    @use_kwargs(request_callable_schema)
    def handler_post_callable_schema(request):
        print(request.data)
        return web.json_response({'msg': 'done', 'data': {}})

    @use_kwargs(request_schema)
    def handler_post_echo(request):
        return web.json_response(request['data'])

    @use_kwargs(request_schema, **locations)
    def handler_get_echo(request):
        print(request.data)
        return web.json_response(request['data'])

    class ViewClass(web.View):
        @docs(
            tags=['mytag'],
            summary='View method summary',
            description='View method description',
        )
        @use_kwargs(request_schema, **locations)
        async def get(self):
            return web.json_response(self.request['data'])

    @use_kwargs(request_schema, **locations)
    def handler_get_echo_old_data(request):
        print(request.data)
        return web.json_response(request.data)

    def other(request):
        return web.Response()

    app = web.Application()
    if nested:
        doc = AiohttpApiSpec(
            title='My Documentation', version='v1', url='/api/docs/api-docs'
        )
        v1 = web.Application()
        v1.router.add_routes(
            [
                web.get('/test', handler_get),
                web.post('/test', handler_post),
                web.post('/test_call', handler_post_callable_schema),
                web.get('/other', other),
                web.get('/echo', handler_get_echo),
                web.view('/class_echo', ViewClass),
                web.get('/echo_old', handler_get_echo_old_data),
                web.post('/echo', handler_post_echo),
            ]
        )
        v1.middlewares.append(aiohttp_apispec_middleware)
        doc.register(v1)
        app.add_subapp('/v1/', v1)
    else:
        doc = AiohttpApiSpec(
            title='My Documentation', version='v1', url='/v1/api/docs/api-docs'
        )
        app.router.add_routes(
            [
                web.get('/v1/test', handler_get),
                web.post('/v1/test', handler_post),
                web.post('/v1/test_call', handler_post_callable_schema),
                web.get('/v1/other', other),
                web.get('/v1/echo', handler_get_echo),
                web.view('/v1/class_echo', ViewClass),
                web.get('/v1/echo_old', handler_get_echo_old_data),
                web.post('/v1/echo', handler_post_echo),
            ]
        )
        app.middlewares.append(aiohttp_apispec_middleware)
        doc.register(app)

    return loop.run_until_complete(test_client(app))
