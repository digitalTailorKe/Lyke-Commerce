# yourapp/management/commands/seed_countries_and_currencies.py
import requests
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Currency, Country
from core.middleware import country_to_currency_data, currency_symbols


class Command(BaseCommand):
    help = 'Seed countries and currencies, and update exchange rates'

    def handle(self, *args, **kwargs):
        # Seed the Currency and Country data
        self.seed_countries_and_currencies()

        # Update exchange rates using CurrencyFreaks API
        self.update_exchange_rates()

    def seed_countries_and_currencies(self):
        currencies_data = currency_symbols[0]['main']['en']['numbers']['currencies']

        for entry in country_to_currency_data:
            country_name = entry['country']
            currency_code = entry['currency_code']
            
            # Get symbol for currency code if available
            currency_data = currencies_data.get(currency_code, {})
            symbol = currency_data.get('symbol', '')
            display_name = currency_data.get('displayName', currency_code)

            # Check if the currency already exists
            currency = Currency.objects.filter(code=currency_code).first()
            
            if currency:
                # Update symbol if it exists and symbol data is available
                if symbol and currency.symbol != symbol:
                    currency.symbol = symbol
                    currency.save(update_fields=['symbol'])
                    self.stdout.write(self.style.SUCCESS(f"Updated symbol for {currency_code}: {symbol}"))
                else:
                    self.stdout.write(self.style.WARNING(f"No symbol update needed for {currency_code}"))
            else:
                # If currency doesn't exist, create it
                currency = Currency.objects.create(
                    code=currency_code,
                    name=display_name,
                    symbol=symbol,
                    exchange_rate_to_usd=Decimal('1.0')  # Temporary, updated by API
                )
                self.stdout.write(self.style.SUCCESS(f"Created new currency {currency_code} with symbol: {symbol}"))

            # Create or update the country
            country, created = Country.objects.get_or_create(
                name=country_name,
                defaults={'currency': currency}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created country: {country_name} with currency {currency_code}"))
            else:
                self.stdout.write(self.style.WARNING(f"Country {country_name} already exists."))


    def update_exchange_rates(self):
        # Fetch exchange rates from the CurrencyFreaks API
        api_key = settings.CURRENCYFREAKS_API_KEY
        CURRENCY_API_URL = 'https://api.currencyfreaks.com/latest'

        try:
            response = requests.get(CURRENCY_API_URL, params={'apikey': api_key})
            data = response.json()

            if response.status_code == 200 and 'rates' in data:
                rates = data.get('rates', {})
                self.stdout.write(f"Fetched exchange rates for {len(rates)} currencies.")

                # Update each currency's exchange rate
                for currency in Currency.objects.all():
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
