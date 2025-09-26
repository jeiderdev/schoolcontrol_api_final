from .users import router as users_router
from .subjects import router as subjects_router
from .grades import router as grades_router
from .evaluations import router as evaluations_router
from .enrollments import router as enrollments_router

routers = [
    users_router,
    subjects_router,
    grades_router,
    evaluations_router,
    enrollments_router,
]
