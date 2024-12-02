from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    IsAdminLoginView, UserOrdersView, 
    UserPendingOrdersView, UpdateOrderStatusView, home,
    ProductViewSet, OrderViewSet, UserViewSet, CategoryListView, ProductSearchView,
    ProductsByCategoryView, UpdateProductRatingView, AddProductCommentView, CartView,
    WishlistView, SignOutView, GetCurrentUserInfoView, SaveOrderView, UploadImageView,
    AddProductView, UserRegistrationView, UserLoginView, FetchProductCommentsView,
    UpdateCommentStatusView, DataView, PasswordResetRequestView, PasswordResetConfirmView
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('sign-out/', SignOutView.as_view(), name='sign_out'),
    path('is-admin/', IsAdminLoginView.as_view(), name='is_admin'),
    path('get-current-user-info/', GetCurrentUserInfoView.as_view(), name='get_current_user_info'),
    path('user-orders/<str:user_id>/', UserOrdersView.as_view(), name='user_orders'),
    path('user-pending-orders/<str:user_id>/', UserPendingOrdersView.as_view(), name='user_pending_orders'),
    path('update-order-status/<str:order_id>/', UpdateOrderStatusView.as_view(), name='update_order_status'),
    path('save-order/', SaveOrderView.as_view(), name='save_order'),
    path('categories/', CategoryListView.as_view(), name='categories'),
    path('search/', ProductSearchView.as_view(), name='product_search'),
    path('products/category/<str:category>/', ProductsByCategoryView.as_view(), name='products_by_category'),
    path('products/<int:product_id>/rating/', UpdateProductRatingView.as_view(), name='update_product_rating'),
    path('products/<int:product_id>/comment/', AddProductCommentView.as_view(), name='add_product_comment'),
    path('upload-image/', UploadImageView.as_view(), name='upload_image'),
    path('add-product/', AddProductView.as_view(), name='add_product'),
    path('fetch-product-comments/', FetchProductCommentsView.as_view(), name='fetch_product_comments'),
    path('update-comment-status/<str:product_name>/<str:comment_text>/', UpdateCommentStatusView.as_view(), name='update_comment_status'),
    path('data/', DataView.as_view(), name='data'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('reset-password/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm_alias'),
    path('reset-password/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('cart/', CartView.as_view(), name='cart'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'), 
    path('', include(router.urls)),
    path('', home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)