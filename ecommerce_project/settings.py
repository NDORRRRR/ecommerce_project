import os
from pathlib import Path
from django.contrib.messages import constants as messages


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-&)n(ptxbmzgwv&1vpd_t13j!k$!&3+rs3@z)hdj%ack-gypsyu'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', # Pastikan ini ada

    # Allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook', # Jika ingin Facebook juga
    # Anda bisa tambahkan provider lain di sini, contohnya:
    # 'allauth.socialaccount.providers.github',

    'ecommerce',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', # PENTING: Diperlukan oleh allauth
]

ROOT_URLCONF = 'ecommerce_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'allauth.account.context_processors.account',
                'allauth.socialaccount.context_processors.socialaccount',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'ecommerce.User'

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / "static", ]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Allauth Settings
SITE_ID = 1 # PENTING: Pastikan ini diatur

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_LOGIN_METHODS = ['username', 'email']
ACCOUNT_SIGNUP_FIELDS = ['email', 'nama', 'noHP', 'alamat']
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_USERNAME_REQUIRED = True # Biasanya default, tapi pastikan
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email' # Memungkinkan login dengan username atau email
ACCOUNT_EMAIL_VERIFICATION = 'none' # Atau 'mandatory'/'optional' sesuai kebutuhan Anda
ACCOUNT_UNIQUE_EMAIL = True # Pastikan email unik

# Pengaturan spesifik untuk Social Account Providers (misalnya Google)
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         # Untuk versi allauth yang lebih baru, opsi ini mungkin tidak diperlukan
#         # atau sudah diatur secara otomatis.
#         # 'SCOPE': [
#         #     'profile',
#         #     'email',
#         # ],
#         # 'AUTH_PARAMS': {
#         #     'access_type': 'online',
#         # }
#         'APP': {
#             'client_id': 'YOUR_GOOGLE_CLIENT_ID', # Ganti ini!
#             'secret': 'YOUR_GOOGLE_CLIENT_SECRET', # Ganti ini!
#             'key': ''
#         }
#     },
#     'facebook': {
#         # 'METHOD': 'oauth2',
#         # 'SCOPE': ['email', 'public_profile'],
#         # 'VERIFIED_EMAIL': False,
#         # 'APP': {
#         #     'client_id': 'YOUR_FACEBOOK_APP_ID', # Ganti ini!
#         #     'secret': 'YOUR_FACEBOOK_APP_SECRET', # Ganti ini!
#         #     'key': ''
#         # }
#     }
# }


ACCOUNT_FORMS = {
    'signup': 'ecommerce.forms.CustomSignupForm',
}
SOCIALACCOUNT_FORMS = {
    'signup': 'ecommerce.forms.CustomSocialSignupForm',
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"