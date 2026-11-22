"""
Integration tests that run the ComdirectImporter against the fake sample
CSV files in samples/. No real bank data needed.

Sample files use account number 9999999999, so the importer must be
constructed with account_nr='9999999999' for identify() to match.
"""

from pathlib import Path
from decimal import Decimal

import pytest

from importers.comdirect import ComdirectImporter
from beancount.core import data

SAMPLES_DIR = Path(__file__).resolve().parent.parent / 'samples'

ACCOUNT = 'Assets:FakeBank:Checking'
IBAN = 'DE99 1234 1234 1234 1234 99'
ACCOUNT_NR = '9999999999'

SAMPLE_30_TAGE = SAMPLES_DIR / 'umsaetze_9999999999_20240901-1606.csv'
SAMPLE_DATE_RANGE = SAMPLES_DIR / 'umsaetze_9999999999_20240609-1200.csv'


class FakeFile:
    """Minimal stand-in for the file object beancount passes to importers.

    The importer only uses file.name, so a plain path wrapper suffices.
    """

    def __init__(self, path):
        self.name = str(path)


def make_importer():
    return ComdirectImporter(ACCOUNT, IBAN, ACCOUNT_NR)


# --- identify ---------------------------------------------------------------

def test_identify_sample_30_tage():
    assert make_importer().identify(FakeFile(SAMPLE_30_TAGE))


def test_identify_sample_date_range():
    assert make_importer().identify(FakeFile(SAMPLE_DATE_RANGE))


def test_identify_rejects_wrong_account_nr():
    importer = ComdirectImporter(ACCOUNT, IBAN, '0000000000')
    assert not importer.identify(FakeFile(SAMPLE_30_TAGE))


# --- extract: "Zeitraum: 30 Tage" variant -----------------------------------

def test_extract_30_tage_dates():
    importer = make_importer()
    importer.extract(FakeFile(SAMPLE_30_TAGE))
    # end date comes from the filename (2024-09-01), start = end - 30 days
    assert importer.date_end.isoformat() == '2024-09-01'
    assert importer.date_start.isoformat() == '2024-08-02'


def test_extract_30_tage_transactions():
    importer = make_importer()
    entries = importer.extract(FakeFile(SAMPLE_30_TAGE))

    transactions = [e for e in entries if isinstance(e, data.Transaction)]
    balances = [e for e in entries if isinstance(e, data.Balance)]

    assert len(transactions) == 6
    assert len(balances) == 1

    # all transactions post to the configured account
    for txn in transactions:
        assert len(txn.postings) == 1
        assert txn.postings[0].account == ACCOUNT
        assert txn.postings[0].units.currency == 'EUR'

    # spot-check first transaction
    first = transactions[0]
    assert first.date.isoformat() == '2024-08-02'
    assert first.narration == 'REWE SAGT DANKE'
    assert first.postings[0].units.number == Decimal('-45.90')
    assert first.postings[0].units.currency == 'EUR'

    # balance assertion: one day after the statement end date
    assert balances[0].date.isoformat() == '2024-09-02'
    assert balances[0].amount.number == Decimal('7715.11')


def test_extract_30_tage_balance_is_consistent():
    """old balance + sum(transactions) == new balance (as asserted)."""
    importer = make_importer()
    entries = importer.extract(FakeFile(SAMPLE_30_TAGE))

    transactions = [e for e in entries if isinstance(e, data.Transaction)]
    balance = next(e for e in entries if isinstance(e, data.Balance))

    old_balance = Decimal('5000.00')
    total = sum((t.postings[0].units.number for t in transactions), Decimal('0'))
    assert old_balance + total == balance.amount.number


# --- extract: explicit date range variant -----------------------------------

def test_extract_date_range_dates():
    importer = make_importer()
    importer.extract(FakeFile(SAMPLE_DATE_RANGE))
    # both dates come from the header line, not the filename
    assert importer.date_start.isoformat() == '2024-06-01'
    assert importer.date_end.isoformat() == '2024-06-09'


def test_extract_date_range_transactions():
    importer = make_importer()
    entries = importer.extract(FakeFile(SAMPLE_DATE_RANGE))

    transactions = [e for e in entries if isinstance(e, data.Transaction)]
    balance = next(e for e in entries if isinstance(e, data.Balance))

    assert len(transactions) == 4
    assert balance.amount.number == Decimal('4588.30')

    old_balance = Decimal('2218.95')
    total = sum((t.postings[0].units.number for t in transactions), Decimal('0'))
    assert old_balance + total == balance.amount.number


# --- offen (pending) rows are skipped ---------------------------------------

def test_offen_row_is_skipped(tmp_path):
    """A row with Buchungstag='offen' (pending) must not produce a transaction."""
    path = tmp_path / 'umsaetze_9999999999_20240901-1606.csv'
    path.write_text(
        ';\n'
        '"Umsätze Girokonto";"Zeitraum: 30 Tage";\n'
        '"Neuer Kontostand";"100,00 EUR";\n'
        '\n'
        '"Buchungstag";"Wertstellung (Valuta)";"Buchungstext";"Verwendungszweck";"Umsatz in EUR";\n'
        '"01.08.2024";"01.08.2024";"REWE";"Einkauf";"-10,00";\n'
        '"offen";"offen";"PENDING ZAHLUNG";"noch nicht gebucht";"-5,00";\n'
        '"Alter Kontostand";"90,00 EUR";"";"";"";\n',
        encoding='iso-8859-1',
    )
    importer = make_importer()
    entries = importer.extract(FakeFile(path))
    transactions = [e for e in entries if isinstance(e, data.Transaction)]
    assert len(transactions) == 1
    assert transactions[0].narration == 'REWE'
