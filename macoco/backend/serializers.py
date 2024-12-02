from rest_framework import serializers
from .models import CustomUser, Product, Order, OrderItem, Comment
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'is_admin', 'email']
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user



class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    order = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_price', 'status', 'name', 'location', 'phone', 'items',]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)  # Create main Order object
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)  # Assign order to each item
        return order
    
class CommentSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    user_id = serializers.IntegerField(source='user.id')

    class Meta:
        model = Comment
        fields = ['product_name', 'user_id', 'text', 'is_new', 'user']

class ProductSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = '__all__'
        extra_kwargs = {
            'category': {'required': True}  # Ensures category is provided
        }