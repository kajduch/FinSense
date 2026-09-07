from aiohttp import web
import aiohttp_cors
import json
import os

routes = web.RouteTableDef()

# Временное in-memory хранилище (в реальном проекте - БД)
# Ключ: session_id, Значение: данные (transactions, stats, etc)
USER_DATA = {}

@routes.get('/')
async def index(request):
    return web.FileResponse('templates/index.html')

@routes.get('/api/data')
async def get_data(request):
    session_id = request.query.get('session_id')
    if not session_id or session_id not in USER_DATA:
        return web.json_response({"error": "No data found for this session"}, status=404)
    return web.json_response(USER_DATA[session_id])

@routes.post('/api/save')
async def save_data(request):
    data = await request.json()
    session_id = data.get('session_id')
    if session_id:
        USER_DATA[session_id] = data
        return web.json_response({"status": "ok"})
    return web.json_response({"error": "No session_id"}, status=400)

app = web.Application()
app.add_routes(routes)

# CORS (для локальной разработки)
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
})
for route in list(app.router.routes()):
    cors.add(route)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    web.run_app(app, port=8080)
