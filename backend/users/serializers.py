from rest_framework import serializers
from users.models import User



class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "password", "role")

    def validate(self, data):
        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError("Username already exists")

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError("Email already exists")

        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)