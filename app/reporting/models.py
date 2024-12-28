from django.db import models


class ActiveNamedMixin(models.Model):
    """
    A mixin providing common fields for models requiring a name, 
    start date, end date, and an active status.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, null=False)
    description = models.TextField(blank=False, null=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class FundAccount(ActiveNamedMixin):

    currency = models.CharField(max_length=10, null=False)
    account_number = models.IntegerField(null=False, blank=False)


class Portfolio(ActiveNamedMixin):
    """
    A Portfolio can be seen as an account in interactive brokers
    """

    fund_account = models.ForeignKey(FundAccount, on_delete=models.CASCADE)
    currency = models.CharField(max_length=10, null=False)

    def __str__(self):
        return f"{self.name}-{self.fund_account.account_number}"

    class Meta:
        unique_together = ("name",)


class DataField(ActiveNamedMixin):

    class Meta:
        unique_together = ("name",)


class PortfolioData(models.Model):

    id = models.AutoField(primary_key=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    report_date = models.DateField(null=False, blank=False)
    data_field = models.ForeignKey(DataField, on_delete=models.CASCADE)
    value = models.FloatField(null=False, blank=False)

    class Meta:
        unique_together = ("portfolio", "data_field", "report_date",)


class Trade(ActiveNamedMixin):

    ASSET_CLASSES = (
        ("Equities", "Equities"),
        ("FX", "FX"),
        ("Rates", "Rates"),
        ("Collateral", "Collateral"),
        ("Commodities", "Commodities"),
        ("Crypto", "Crypto"),
        ("N/A", "N/A"),
    )

    BUCKETS = (
        ("Global Macro", "Global Macro"),
        ("RV", "RV"),
        ("Volatility", "Volatility"),
        ("Hedge", "Hedge"),
        ("Collateral", "Collateral"),
    )

    ark_trade_id = models.CharField(max_length=10, blank=False, null=False)

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)

    asset_class = models.CharField(
        max_length=30, choices=ASSET_CLASSES, default="Equities"
    )
    bucket = models.CharField(
        max_length=30, choices=BUCKETS, default="Global Macro"
    )
    is_systematic = models.BooleanField(default=False)
    currency = models.CharField(max_length=10, null=False)

    class Meta:
        unique_together = ("ark_trade_id",)


class Instrument(ActiveNamedMixin):

    SECURITY_TYPES = (("ADR", "ADR"),
                      ("BOND", "BOND"),
                      ("COMMON", "COMMON"),
                      ("ETF", "ETF"),
                      ("OPTION", "OPTION"),
                      ("FUTURES", "FUTURES"),
                      ("WARRANT", "WARRANT"),
                      )

    conid = models.IntegerField(blank=False, null=False)
    symbol = models.CharField(max_length=20, null=False, blank=False)
    currency = models.CharField(max_length=10, null=False)
    isin = models.CharField(max_length=20, null=True, blank=True)
    sec_type = models.CharField(
        max_length=30, choices=SECURITY_TYPES, default="COMMON"
    )
    trading_exchange = models.CharField(max_length=20, null=False, blank=False)
    strike = models.FloatField(blank=True, null=True)
    expiry = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("conid", "symbol",)


class Position(ActiveNamedMixin):

    trade = models.ForeignKey(Trade, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("trade", "instrument", )


class PositionData(ActiveNamedMixin):

    report_date = models.DateField(null=False, blank=False)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    units = models.IntegerField(blank=False, null=False)
    market_price = models.FloatField(blank=False, null=False)
    average_cost = models.FloatField(blank=False, null=False)
    mtm_pnl = models.FloatField(blank=False, null=False)
    unrealized_pnl = models.FloatField(blank=False, null=False)
    realized_pnl = models.FloatField(blank=False, null=False)
    transaction_pnl = models.FloatField(blank=False, null=False)
    commission = models.FloatField(blank=False, null=False)
    other_fees = models.FloatField(blank=False, null=False)

    class Meta:
        unique_together = ("report_date", "position",)
