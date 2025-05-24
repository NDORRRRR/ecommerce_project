from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ecommerce.models import Buyer

User = get_user_model()

class Command(BaseCommand):
    help = 'Create missing Buyer objects for existing users'

    def handle(self, *args, **options):
        self.stdout.write('Checking for users without Buyer objects...')
        
        # Get all users that are not admin/staff and don't have Buyer objects
        users_without_buyer = User.objects.filter(
            is_staff=False, 
            is_superuser=False
        ).exclude(
            id__in=Buyer.objects.values_list('user_id', flat=True)
        )
        
        created_count = 0
        for user in users_without_buyer:
            Buyer.objects.create(user=user)
            created_count += 1
            self.stdout.write(f'Created Buyer for user: {user.username}')
        
        if created_count == 0:
            self.stdout.write(self.style.SUCCESS('All users already have Buyer objects!'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} Buyer objects!')
            )