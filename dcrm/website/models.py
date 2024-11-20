from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# Create your models here.

class Company(models.Model):
    companyid = models.CharField(max_length=255, unique=True, null=True)
    company_name = models.CharField(max_length=255)
    company_email = models.EmailField(max_length=255)
    company_website = models.URLField(max_length=255, null=True, blank=True)
    company_address = models.TextField()
    confirm = models.BooleanField(default=False)
    

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # user.set_password(password)  # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    company = models.ForeignKey("Company", on_delete=models.CASCADE, related_name="users", null=True, to_field="companyid")
    userid = models.CharField(max_length=128, unique=True, null=True)
    email = models.EmailField(max_length=128, unique=True)
    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)
    role = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"  # Use email for authentication
    REQUIRED_FIELDS = []  # Add required fields here if necessary
    
    def has_perm(self, perm, obj=None):
        """
        Does the user have a specific permission?
        """
        return self.is_superuser

    def has_module_perms(self, app_label):
        """
        Does the user have permissions to view the app `app_label`?
        """
        return self.is_superuser

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"