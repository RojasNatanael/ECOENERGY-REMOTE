import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from organizations.models import Organization
from devices.models import Category, Product, Zone, Device, Measurement, AlertRule, ProductAlertRule

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with test data for devices app'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Create organizations if they don't exist
        org1, created = Organization.objects.get_or_create(
            name="TechCorp Inc.",
            defaults={'is_active': True}
        )
        
        org2, created = Organization.objects.get_or_create(
            name="SmartOffice Ltd.", 
            defaults={'is_active': True}
        )
        
        # Create categories
        categories_data = [
            {"name": "Computers"},
            {"name": "HVAC"},
            {"name": "Lighting"}, 
            {"name": "Sensors"},
            {"name": "Office Equipment"},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={"status": "ACTIVE"}
            )
            categories[cat_data["name"]] = category
            self.stdout.write(f'Created category: {category.name}')

        # Create products (device models/templates)
        products_data = [
            {
                "name": "Dell OptiPlex 3090",
                "category": categories["Computers"],
                "sku": "DEL-OPT-3090",
                "manufacturer": "Dell",
                "model_name": "OptiPlex 3090",
                "description": "Business desktop computer",
                "nominal_voltage_v": 220,
                "max_current_a": 3.5,
                "standby_power_w": 15.5,
            },
            {
                "name": "HP EliteDesk 800 G6", 
                "category": categories["Computers"],
                "sku": "HP-ELITE-800G6",
                "manufacturer": "HP",
                "model_name": "EliteDesk 800 G6",
                "description": "High-performance business desktop",
                "nominal_voltage_v": 220,
                "max_current_a": 4.2,
                "standby_power_w": 18.2,
            },
            {
                "name": "Daikin VRV System",
                "category": categories["HVAC"],
                "sku": "DAI-VRV-5000",
                "manufacturer": "Daikin",
                "model_name": "VRV 5000",
                "description": "Variable Refrigerant Volume HVAC system",
                "nominal_voltage_v": 380,
                "max_current_a": 25.0,
                "standby_power_w": 45.0,
            },
            {
                "name": "Philips Smart LED Panel",
                "category": categories["Lighting"],
                "sku": "PHI-LED-P60",
                "manufacturer": "Philips",
                "model_name": "Smart LED Panel 60x60",
                "description": "Smart lighting panel with sensors",
                "nominal_voltage_v": 220,
                "max_current_a": 0.8,
                "standby_power_w": 2.5,
            },
            {
                "name": "Energy Monitor Sensor",
                "category": categories["Sensors"],
                "sku": "EMON-PI-V2",
                "manufacturer": "OpenEnergy",
                "model_name": "emonPi v2",
                "description": "Open source energy monitoring sensor",
                "nominal_voltage_v": 5,
                "max_current_a": 0.5,
                "standby_power_w": 1.2,
            },
            {
                "name": "Xerox WorkCentre 6025",
                "category": categories["Office Equipment"],
                "sku": "XER-WC-6025",
                "manufacturer": "Xerox",
                "model_name": "WorkCentre 6025",
                "description": "Multifunction printer/copier/scanner",
                "nominal_voltage_v": 220,
                "max_current_a": 8.5,
                "standby_power_w": 35.0,
            },
        ]

        products = {}
        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                sku=prod_data["sku"],
                defaults={
                    "name": prod_data["name"],
                    "category": prod_data["category"],
                    "manufacturer": prod_data["manufacturer"],
                    "model_name": prod_data["model_name"],
                    "description": prod_data["description"],
                    "nominal_voltage_v": prod_data["nominal_voltage_v"],
                    "max_current_a": prod_data["max_current_a"],
                    "standby_power_w": prod_data["standby_power_w"],
                    "status": "ACTIVE"
                }
            )
            products[prod_data["sku"]] = product
            self.stdout.write(f'Created product: {product.name}')

        # Create zones for organizations
        zones_data = [
            {"organization": org1, "name": "Main Office"},
            {"organization": org1, "name": "Server Room"},
            {"organization": org1, "name": "Meeting Rooms"},
            {"organization": org2, "name": "Floor 1 - Open Space"},
            {"organization": org2, "name": "Floor 2 - Private Offices"},
            {"organization": org2, "name": "Floor 2 - Conference Area"},
        ]

        zones = {}
        for zone_data in zones_data:
            zone, created = Zone.objects.get_or_create(
                organization=zone_data["organization"],
                name=zone_data["name"],
                defaults={"status": "ACTIVE"}
            )
            zones[f"{zone_data['organization'].name} - {zone_data['name']}"] = zone
            self.stdout.write(f'Created zone: {zone.name} @ {zone.organization.name}')

        # Create devices (multiple devices of the same product/model)
        devices_data = [
            # TechCorp Inc. devices
            {"organization": org1, "zone": zones["TechCorp Inc. - Main Office"], "product": products["DEL-OPT-3090"], "name": "PC-Reception", "max_power_w": 350, "serial_number": "DEL001"},
            {"organization": org1, "zone": zones["TechCorp Inc. - Main Office"], "product": products["DEL-OPT-3090"], "name": "PC-Admin-01", "max_power_w": 350, "serial_number": "DEL002"},
            {"organization": org1, "zone": zones["TechCorp Inc. - Main Office"], "product": products["DEL-OPT-3090"], "name": "PC-Admin-02", "max_power_w": 350, "serial_number": "DEL003"},
            {"organization": org1, "zone": zones["TechCorp Inc. - Server Room"], "product": products["HP-ELITE-800G6"], "name": "Server-01", "max_power_w": 450, "serial_number": "HP001"},
            {"organization": org1, "zone": zones["TechCorp Inc. - Server Room"], "product": products["HP-ELITE-800G6"], "name": "Server-02", "max_power_w": 450, "serial_number": "HP002"},
            {"organization": org1, "zone": zones["TechCorp Inc. - Meeting Rooms"], "product": products["PHI-LED-P60"], "name": "Light-Main-Room", "max_power_w": 60, "serial_number": "PHI001"},
            {"organization": org1, "zone": zones["TechCorp Inc. - Main Office"], "product": products["XER-WC-6025"], "name": "Printer-Main", "max_power_w": 1500, "serial_number": "XER001"},
            {"organization": org1, "zone": zones["TechCorp Inc. - Server Room"], "product": products["EMON-PI-V2"], "name": "Energy-Sensor-Room", "max_power_w": 5, "serial_number": "EMON001"},

            # SmartOffice Ltd. devices  
            {"organization": org2, "zone": zones["SmartOffice Ltd. - Floor 1 - Open Space"], "product": products["DEL-OPT-3090"], "name": "PC-OpenSpace-01", "max_power_w": 350, "serial_number": "DEL101"},
            {"organization": org2, "zone": zones["SmartOffice Ltd. - Floor 1 - Open Space"], "product": products["DEL-OPT-3090"], "name": "PC-OpenSpace-02", "max_power_w": 350, "serial_number": "DEL102"},
            {"organization": org2, "zone": zones["SmartOffice Ltd. - Floor 2 - Private Offices"], "product": products["HP-ELITE-800G6"], "name": "PC-Manager-01", "max_power_w": 450, "serial_number": "HP101"},
            {"organization": org2, "zone": zones["SmartOffice Ltd. - Floor 2 - Private Offices"], "product": products["HP-ELITE-800G6"], "name": "PC-Manager-02", "max_power_w": 450, "serial_number": "HP102"},
            {"organization": org2, "zone": zones["SmartOffice Ltd. - Floor 2 - Conference Area"], "product": products["PHI-LED-P60"], "name": "Light-Conference", "max_power_w": 60, "serial_number": "PHI101"},
            {"organization": org2, "zone": zones["SmartOffice Ltd. - Floor 1 - Open Space"], "product": products["DAI-VRV-5000"], "name": "AC-Main-Floor", "max_power_w": 5000, "serial_number": "DAI101"},
            {"organization": org2, "zone": zones["SmartOffice Ltd. - Floor 1 - Open Space"], "product": products["XER-WC-6025"], "name": "Printer-Floor1", "max_power_w": 1500, "serial_number": "XER101"},
            {"organization": org2, "zone": zones["SmartOffice Ltd. - Floor 2 - Conference Area"], "product": products["EMON-PI-V2"], "name": "Energy-Sensor-Conf", "max_power_w": 5, "serial_number": "EMON101"},
        ]

        devices = []
        for dev_data in devices_data:
            device, created = Device.objects.get_or_create(
                organization=dev_data["organization"],
                name=dev_data["name"],
                defaults={
                    "zone": dev_data["zone"],
                    "product": dev_data["product"],
                    "max_power_w": dev_data["max_power_w"],
                    "serial_number": dev_data["serial_number"],
                    "status": "ACTIVE"
                }
            )
            devices.append(device)
            self.stdout.write(f'Created device: {device.name} @ {device.organization.name}')

        # Create alert rules
        alert_rules_data = [
            {"name": "High Energy Consumption", "severity": "HIGH", "unit": "kWh", "default_min_threshold": None, "default_max_threshold": 10.0},
            {"name": "Critical Power Overload", "severity": "CRITICAL", "unit": "kWh", "default_min_threshold": None, "default_max_threshold": 15.0},
            {"name": "Low Energy Usage", "severity": "LOW", "unit": "kWh", "default_min_threshold": 0.1, "default_max_threshold": None},
            {"name": "Standby Power Alert", "severity": "MEDIUM", "unit": "W", "default_min_threshold": None, "default_max_threshold": 50.0},
        ]

        alert_rules = {}
        for rule_data in alert_rules_data:
            rule, created = AlertRule.objects.get_or_create(
                name=rule_data["name"],
                severity=rule_data["severity"],
                defaults={
                    "unit": rule_data["unit"],
                    "default_min_threshold": rule_data["default_min_threshold"],
                    "default_max_threshold": rule_data["default_max_threshold"],
                    "status": "ACTIVE"
                }
            )
            alert_rules[rule_data["name"]] = rule
            self.stdout.write(f'Created alert rule: {rule.name} [{rule.severity}]')

        # Create product-specific alert rule overrides
        product_alert_data = [
            {"product": products["XER-WC-6025"], "alert_rule": alert_rules["High Energy Consumption"], "min_threshold": None, "max_threshold": 8.0},
            {"product": products["DAI-VRV-5000"], "alert_rule": alert_rules["Critical Power Overload"], "min_threshold": None, "max_threshold": 25.0},
            {"product": products["EMON-PI-V2"], "alert_rule": alert_rules["Low Energy Usage"], "min_threshold": 0.01, "max_threshold": None},
        ]

        for par_data in product_alert_data:
            par, created = ProductAlertRule.objects.get_or_create(
                product=par_data["product"],
                alert_rule=par_data["alert_rule"],
                defaults={
                    "min_threshold": par_data["min_threshold"],
                    "max_threshold": par_data["max_threshold"],
                    "status": "ACTIVE"
                }
            )
            self.stdout.write(f'Created product alert rule: {par.product.name} - {par.alert_rule.name}')

        # Create sample measurements for some devices
        self.stdout.write('Creating sample measurements...')
        for device in random.sample(devices, 8):  # Create measurements for 8 random devices
            for i in range(10):  # 10 measurements per device
                # Create realistic energy values based on device type
                if device.product.category.name == "Computers":
                    base_energy = random.uniform(0.5, 3.0)
                elif device.product.category.name == "HVAC":
                    base_energy = random.uniform(5.0, 20.0)
                elif device.product.category.name == "Lighting":
                    base_energy = random.uniform(0.1, 1.0)
                elif device.product.category.name == "Office Equipment":
                    base_energy = random.uniform(0.5, 8.0)
                else:
                    base_energy = random.uniform(0.01, 0.5)
                
                # Add some random variation
                energy_kwh = round(base_energy + random.uniform(-0.2, 0.2), 3)
                
                # Occasionally trigger an alert
                triggered_alert = None
                if random.random() < 0.1:  # 10% chance of alert
                    triggered_alert = random.choice(list(alert_rules.values()))
                
                measurement = Measurement.objects.create(
                    device=device,
                    energy_kwh=energy_kwh,
                    triggered_alert=triggered_alert,
                    status="ACTIVE"
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test data:\n'
                f'- {Category.objects.count()} categories\n'
                f'- {Product.objects.count()} products\n' 
                f'- {Zone.objects.count()} zones\n'
                f'- {Device.objects.count()} devices\n'
                f'- {Measurement.objects.count()} measurements\n'
                f'- {AlertRule.objects.count()} alert rules\n'
                f'- {ProductAlertRule.objects.count()} product alert rules'
            )
        )