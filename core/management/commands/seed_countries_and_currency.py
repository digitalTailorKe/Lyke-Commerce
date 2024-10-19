# yourapp/management/commands/seed_countries_and_currencies.py
import requests
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Currency, Country
from core.middleware import country_to_currency_data

# Step 1: Predefined country-to-currency data

# Step 2: URL for fetching exchange rates
CURRENCY_API_URL = 'https://api.currencyfreaks.com/latest'

class Command(BaseCommand):
    help = 'Seed countries and currencies, and update exchange rates'

    def handle(self, *args, **kwargs):
        # Step 3: Seed the Currency and Country data
        self.seed_countries_and_currencies()

        # Step 4: Update exchange rates using CurrencyFreaks API
        self.update_exchange_rates()

    def seed_countries_and_currencies(self):
        for entry in country_to_currency_data:
            country_name = entry['country']
            currency_code = entry['currency_code']

            # Check if the currency exists, if not, create it
            currency, created = Currency.objects.get_or_create(
                code=currency_code,
                defaults={
                    'name': currency_code,  # You can customize the name or use the code as a placeholder
                    'exchange_rate_to_usd': Decimal('1.0'),  # Temporary, will be updated by API
                }
            )

            # Check if the country exists, if not, create it
            country, created = Country.objects.get_or_create(
                name=country_name,
                defaults={
                    'currency': currency
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created country: {country_name} with currency {currency_code}"))
            else:
                self.stdout.write(self.style.WARNING(f"Country {country_name} already exists."))

    def update_exchange_rates(self):
        # Fetch exchange rates from the CurrencyFreaks API
        api_key = settings.CURRENCYFREAKS_API_KEY

        try:
            response = requests.get(CURRENCY_API_URL, params={'apikey': api_key})
            data = response.json()

            if response.status_code == 200 and 'rates' in data:
                rates = data.get('rates', {})
                print(rates)
                self.stdout.write(f"Fetched exchange rates for {len(rates)} currencies.")

                # Iterate through the currencies in the database
                for currency in Currency.objects.all():
                    # Update the currency's exchange rate if it's available in the API response
                    exchange_rate = rates.get(currency.code)

                    if exchange_rate:
                        currency.exchange_rate_to_usd = Decimal(exchange_rate)
                        
                        currency.save()

                        self.stdout.write(self.style.SUCCESS(f"Updated {currency.name} ({currency.code}): Rate {currency.exchange_rate_to_usd}, Symbol {currency.symbol}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"Exchange rate not found for {currency.name} ({currency.code})"))

            else:
                self.stdout.write(self.style.ERROR("Failed to fetch data from CurrencyFreaks API."))

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"CurrencyFreaks API Error: {e}"))

    def get_currency_symbol(self, currency_code):
        # This is a simplified mapping of currency codes to symbols
        currency_symbols = {
            "USD": "$", "CAD": "C$", "EUR": "€", "GBP": "£", "JPY": "¥",
            "CHF": "Fr", "AUD": "A$", "INR": "₹", "CNY": "¥", "AFN": "؋",
            "ALL": "L", "DZD": "دج", "AOA": "Kz", "ARS": "$", "BHD": ".د.ب",
            # Add more symbols as necessary...
        }
        return currency_symbols.get(currency_code, '')  # Default to empty string if symbol not found
