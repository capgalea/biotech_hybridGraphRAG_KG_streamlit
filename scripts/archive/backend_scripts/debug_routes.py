import app.routers.analytics as analytics
print(f"File: {analytics.__file__}")
for route in analytics.router.routes:
    print(f"Path: {route.path}, Name: {route.name}")
