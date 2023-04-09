from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group
import re
from django.utils import timezone
from rest_framework import permissions
from ckeditor_uploader.fields import RichTextUploadingField


def isValid(s):
    Pattern = re.compile("(0|91)?[6-9][0-9]{9}")
    return Pattern.match(s)


YEARS = (
    ("FIRST", "1st year"),
    ("SECOND", "2nd year"),
    ("THIRD", "3rd year"),
    ("FORTH", "4th year"),
    ("FIFTH", "5th year"),
)


class AccountManager(BaseUserManager):
    def create_user(self, email, password="Random"):
        if not email:
            raise ValueError("The Email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(password=password, email=self.normalize_email(email))
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class UserAcount(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    college_name = models.CharField(max_length=200, blank=False, null=False)
    year = models.CharField(max_length=20, choices=YEARS, blank=False, null=False)
    phone_number = models.CharField(
        validators=[isValid], max_length=16, blank=False, null=False
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    radianite_points = models.BigIntegerField(default=0, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = AccountManager()

    def _str_(self):
        return f"{self.email}"

    def has_perm(self, perm, obj=None):
        if "." in perm:
            perm = perm.split(".")[1]
        if self.is_admin:
            return True
        if self.is_staff and perm in self.get_all_permissions():
            return True
        return False

    # # return all the user permission
    def get_all_permissions(self, obj=None):
        all_perm = []
        if self.group is None:
            return all_perm
        for perm in self.group.permissions.all():
            all_perm.append(perm.codename)
        return all_perm

    def has_module_perms(self, app_label):
        return True


class BroadCast_Email(models.Model):
    permission_classes = (permissions.IsAuthenticated,)
    subject = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)
    message = RichTextUploadingField()

    def __unicode__(self):
        return self.subject

    class Meta:
        verbose_name = "BroadCast Email to all Member"
        verbose_name_plural = "BroadCast Email"
