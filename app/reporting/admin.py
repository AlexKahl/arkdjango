from django.contrib import admin
from .models import FundAccount, Portfolio, Trade

# Register your models here.


@admin.register(FundAccount)
class FundAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "account_number", "currency", "name", "description",
                    "start_date", "end_date", "is_active")
    readonly_fields = ("id",)
    search_fields = ("id", "account_number", "currency")


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "fund_account__acount_number", "currency",
                    "description", "start_date", "end_date", "is_active")
    readonly_fields = ("id",)
    search_fields = ("id", "name", "currency")


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("id", "ark_trade_id",
                    "name", "description", "currency",
                    "asset_class", "bucket", "is_systematic",
                    "start_date", "end_date", "is_active")
    readonly_fields = ("id",)
    search_fields = ("id", "name", "ark_trade_id", "asset_class", "bucket")
