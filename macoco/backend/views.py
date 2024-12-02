from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from .models import Product, Order, Comment
from .serializers import UserSerializer, ProductSerializer, OrderSerializer, CommentSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .forms import ProductForm
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, render, redirect
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import logging
from .serializers import UserRegistrationSerializer


logger = logging.getLogger(__name__)
User = get_user_model()

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                'user_id': str(user.id),
                'username': user.username,
                'email': user.email,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class SignOutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'User signed out'}, status=status.HTTP_200_OK)

class IsAdminLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None and user.is_staff:
            refresh = RefreshToken.for_user(user)
            return Response({
                'is_admin': True,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
        return Response({'is_admin': False}, status=status.HTTP_401_UNAUTHORIZED)

class GetCurrentUserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            return Response({
                'user_id': str(user.id),
                'username': user.username,
                'email': user.email
            }, status=200)
        return Response({'detail': 'Not authenticated'}, status=401)
        
class AddProductView(APIView):
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)  # Add this line to print the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
class UploadImageView(APIView):
    def post(self, request):
        file = request.FILES.get('image')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        file_name = default_storage.save(file.name, ContentFile(file.read()))
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        print(f"File saved at: {file_path}")  # Print the file path for debugging
        file_url = request.build_absolute_uri(default_storage.url(file_name))
        
        return Response({'imageUrl': file_url}, status=status.HTTP_200_OK)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = request.user
        if str(user.id) != user_id:
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        orders = Order.objects.filter(user=user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class UserPendingOrdersView(APIView):
    def get(self, request, user_id):
        orders = Order.objects.filter(user_id=user_id, status='pending')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class SaveOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        items = request.data.get('items', [])
        total_price = request.data.get('total_price', 0)

        if not items:
            return Response({'detail': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)

        order_data = {
            'user': user.id,
            'total_price': total_price,
            'items': [{'product': item['product_id'], 'quantity': item['quantity'], 'price': item['price']} for item in items],
        }

        serializer = OrderSerializer(data=order_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            order.status = request.data.get('status', order.status)
            order.save()
            return Response({'detail': 'Order status updated'}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        

        
def home(request):
    return HttpResponse("Welcome to the Macoco App API")

class CategoryListView(APIView):
    def get(self, request):
        categories = Product.objects.values_list('category', flat=True).distinct()
        return Response(categories)
    
class ProductSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        if query:
            products = Product.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        return Response([], status=status.HTTP_200_OK)
    
class ProductsByCategoryView(APIView):
    def get(self, request, category):
        products = Product.objects.filter(category=category)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
class UpdateProductRatingView(APIView):
    def post(self, request, product_id):
        rating = request.data.get('rating')
        try:
            product = Product.objects.get(id=product_id)
            product.rating = float(rating)  # Ensure rating is handled as a float
            product.save()
            return Response({'detail': 'Product rating updated'}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

class AddProductCommentView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            user = request.user if request.user.is_authenticated else None
            text = request.data.get('comment')
            if text:
                comment = Comment.objects.create(product=product, user=user, text=text)
                return Response({'detail': 'Comment added successfully'}, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Comment text not provided'}, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
class FetchProductCommentsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            comments = Comment.objects.filter(product=product)
            comments_data = [{'user': comment.user.username if comment.user else 'Anonymous', 'text': comment.text} for comment in comments]
            return Response(comments_data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
class CartView(APIView):
    def post(self, request):
        # Add item to cart
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        try:
            product = Product.objects.get(id=product_id)
            # Assuming you have a Cart model or similar logic to handle cart items
            # Here you would add the product to the user's cart
            # For simplicity, let's assume we just return the product details
            return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        # Retrieve cart items
        # Assuming you have a Cart model or similar logic to handle cart items
        # Here you would retrieve the cart items for the user
        # For simplicity, let's assume we just return a list of products
        products = Product.objects.all()  # Replace with actual cart retrieval logic
        return Response(ProductSerializer(products, many=True).data, status=status.HTTP_200_OK)
    
    def put(self, request):
        # Update cart item quantity
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        try:
            product = Product.objects.get(id=product_id)
            # Assuming you have a Cart model or similar logic to handle cart items
            # Here you would update the quantity of the product in the user's cart
            # For simplicity, let's assume we just return the product details
            return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
class WishlistView(APIView):
    def post(self, request):
        # Add item to wishlist
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            # Assuming you have a Wishlist model or similar logic to handle wishlist items
            # Here you would add the product to the user's wishlist
            # For simplicity, let's assume we just return the product details
            return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        # Remove item from wishlist
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            # Assuming you have a Wishlist model or similar logic to handle wishlist items
            # Here you would remove the product from the user's wishlist
            # For simplicity, let's assume we just return a success message
            return Response({'detail': 'Product removed from wishlist'}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    def get(self, request):
        # Retrieve wishlist items
        # Assuming you have a Wishlist model or similar logic to handle wishlist items
        # Here you would retrieve the wishlist items for the user
        # For simplicity, let's assume we just return a list of products
        products = Product.objects.all()  # Replace with actual wishlist retrieval logic
        return Response(ProductSerializer(products, many=True).data, status=status.HTTP_200_OK)
    
class FetchProductCommentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

def is_admin(user):
    return user.is_authenticated and user.is_admin

def is_admin(user):
    return user.is_authenticated and user.is_admin

@user_passes_test(is_admin)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Redirect to a page that lists products
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

class UpdateCommentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, product_name, comment_text):
        try:
            comment = Comment.objects.get(product__name=product_name, text=comment_text)
            comment.is_new = False
            comment.save()
            return Response({'detail': 'Comment status updated'}, status=status.HTTP_200_OK)
        except Comment.DoesNotExist:
            return Response({'detail': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)
        
class DataView(APIView):
    def get(self, request):
        products = Product.objects.all()
        products_data = ProductSerializer(products, many=True).data
        print(products_data)
        return Response(products_data, status=status.HTTP_200_OK)
    
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        if not email or not username:
            return Response({'error': 'Email and username are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email, username=username)
        except User.DoesNotExist:
            return Response({'error': 'User with this email and username does not exist'}, status=status.HTTP_404_NOT_FOUND)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        email_body = f"Hi {user.username},\n\nYou requested a password reset. Use the following token to reset your password:\nToken: {token}\nUID: {uid}\n\nIf you did not request a password reset, please ignore this email."

        send_mail(
            'Password Reset Request',
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )

        return Response({'message': 'Password reset email sent', 'uid': uid, 'token': token}, status=status.HTTP_200_OK)
    
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        password = request.data.get('password')
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid token or user ID'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.set_password(password)
            user.save()
            return Response({'message': 'Password has been reset'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
