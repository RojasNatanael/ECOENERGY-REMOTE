import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from organizations.models import Organization, Usuario

class Command(BaseCommand):
    help = 'Populate database with test data'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Create Groups
        groups_data = [
            {'name': 'Encargado EcoEnergy'},
            {'name': 'Cliente Admin'}, 
            {'name': 'Cliente Electrónico'},
        ]
        
        groups = {}
        for group_data in groups_data:
            group, created = Group.objects.get_or_create(name=group_data['name'])
            groups[group_data['name']] = group
            self.stdout.write(f'Created group: {group.name}')

        # Create Organizations
        organizations_data = [
            {'name': 'TechCorp Solutions'},
            {'name': 'GreenEnergy Inc'},
            {'name': 'SmartBuildings Co'},
            {'name': 'EcoPower Systems'},
            {'name': 'InnovateTech Labs'},
        ]
        
        organizations = []
        for org_data in organizations_data:
            org, created = Organization.objects.get_or_create(name=org_data['name'])
            organizations.append(org)
            self.stdout.write(f'Created organization: {org.name}')

        # Create Users with Usuario profiles
        users_data = [
            # Encargado EcoEnergy users
            {
                'username': 'admin.ecoenergy',
                'email': 'admin@ecoenergy.com',
                'password': 'testpass123',
                'name': 'María González',
                'phone': '555123456',
                'organization': 'TechCorp Solutions',
                'group': 'Encargado EcoEnergy'
            },
            {
                'username': 'supervisor.energy',
                'email': 'supervisor@ecoenergy.com', 
                'password': 'testpass123',
                'name': 'Carlos Rodríguez',
                'phone': '555123457',
                'organization': 'GreenEnergy Inc',
                'group': 'Encargado EcoEnergy'
            },
            
            # Cliente Admin users
            {
                'username': 'admin.techcorp',
                'email': 'admin@techcorp.com',
                'password': 'testpass123', 
                'name': 'Ana Martínez',
                'phone': '555123458',
                'organization': 'TechCorp Solutions',
                'group': 'Cliente Admin'
            },
            {
                'username': 'admin.green',
                'email': 'admin@greenenergy.com',
                'password': 'testpass123',
                'name': 'David López',
                'phone': '555123459', 
                'organization': 'GreenEnergy Inc',
                'group': 'Cliente Admin'
            },
            
            # Cliente Electrónico users
            {
                'username': 'user.tech1',
                'email': 'user1@techcorp.com',
                'password': 'testpass123',
                'name': 'Laura Sánchez',
                'phone': '555123460',
                'organization': 'TechCorp Solutions', 
                'group': 'Cliente Electrónico'
            },
            {
                'username': 'user.tech2',
                'email': 'user2@techcorp.com',
                'password': 'testpass123',
                'name': 'Pedro Ramírez',
                'phone': '555123461',
                'organization': 'TechCorp Solutions',
                'group': 'Cliente Electrónico'
            },
            {
                'username': 'user.green1',
                'email': 'user1@greenenergy.com',
                'password': 'testpass123',
                'name': 'Sofía Herrera',
                'phone': '555123462',
                'organization': 'GreenEnergy Inc',
                'group': 'Cliente Electrónico'
            },
            {
                'username': 'user.smart1',
                'email': 'user1@smartbuildings.com',
                'password': 'testpass123',
                'name': 'Jorge Mendoza',
                'phone': '555123463',
                'organization': 'SmartBuildings Co',
                'group': 'Cliente Electrónico'
            },
            {
                'username': 'user.ecopower1',
                'email': 'user1@ecopower.com',
                'password': 'testpass123',
                'name': 'Elena Castro',
                'phone': '555123464',
                'organization': 'EcoPower Systems',
                'group': 'Cliente Electrónico'
            },
            {
                'username': 'user.innovate1',
                'email': 'user1@innovatetech.com',
                'password': 'testpass123',
                'name': 'Roberto Silva',
                'phone': '555123465',
                'organization': 'InnovateTech Labs',
                'group': 'Cliente Electrónico'
            },
        ]

        for user_data in users_data:
            # Create User
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'is_active': True
                }
            )
            user.set_password(user_data['password'])
            user.save()

            # Get organization and group
            organization = Organization.objects.get(name=user_data['organization'])
            group = groups[user_data['group']]

            # Add user to group
            user.groups.add(group)

            # Create Usuario profile
            usuario, created = Usuario.objects.get_or_create(
                user=user,
                defaults={
                    'name': user_data['name'],
                    'phone': user_data['phone'],
                    'organization': organization
                }
            )

            if created:
                self.stdout.write(f'Created user: {user.username} ({user_data["group"]})')
            else:
                self.stdout.write(f'Updated user: {user.username}')

        self.stdout.write(self.style.SUCCESS('Successfully populated database with test data!'))