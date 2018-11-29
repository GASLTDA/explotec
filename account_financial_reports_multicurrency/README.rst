.. image:: https://img.shields.io/badge/licence-LGPL--3-yellow.svg
    :alt: License: LGPL-3

Account Financial Reports Multicurrency
=======================================

Make financial reports for your bussiness group using the IFRS standard for
consolidations in foreign currencies.

Summary
-------

This module let you build the financial reports for your group of companies that
operates in different currencies, preparing the consolidation of the statements
of two or more companies based on the IFRS standard (`IAS 21 The Effects of Changes in Foreign Exchange Rates
<https://www.ifrs.org/issued-standards/list-of-standards/ias-21-the-effects-of-changes-in-foreign-exchange-rates/>`_)
that states:

  For translation into the functional currency or into a presentation
  currency, the following procedures apply, except in limited
  circumstances:

  - assets and liabilities are translated at the exchange rate at the
    end of the period;
  - income and expenses are translated at exchange rates at the dates
    of the transactions; and
  - resulting exchange differences are recognised in other
    comprehensive income and reclassified to profit or
    loss on disposal of the related foreign operation.

How to configure it
-------------------

Here we describe how you can configure your instance with an example. In this
example we have two companies "Holding Company" and "Your Company", they
operate in different functional currencies, EUR and USD respectively.

In "Your Company", the one with USD as functional currency, we have a ledger
like this:

.. image:: static/description/img-shot-02.png

In "Holding Company", that is the Consolidating Company with EUR as functional
currency, we have exchange rates for each currency as these:

.. image:: static/description/img-shot-03.png
.. image:: static/description/img-shot-04.png

For that
we will create two new custom reports.

- Enable Multi-currency setting in Odoo database.
- Enter in debug mode to be able to create your custom report.
- Go to ``Accounting > Configuration > Financial Reports``.

Creating report "My Receivables":

- Create a new Report and call it "My Receivables".
- Uncheck the option "Based on date ranges".
- Add a line to the report and call it Receivables, with next parameters:

  - Formula: ``balance = sum.balance``
  - Domain: ``[('account_id', '=', '101200')]``
  - Level: ``1``

Creating report "My Incomes":

- Create a new Report and call it "My Incomes".
- Add a line to the report and call it Receivables, with next parameters:

  - Formula: ``balance = sum.credit``
  - Domain: ``[('account_id', '=', '200000')]``
  - Level: ``1``

Refresh your browser to be sure the reports was created at the
``Accounting > Reporting`` menu.


How to use it
-------------

The next steps are based on the example reports configured in the above section.

For assets:

- Go to ``Accounting > Reporting > My Receivables`` (My Receivables or whatever
  name you used for your report)
- In the filter options select:

  - As of ``End of Last Quarter``.
  - In ``Comparison > Previous Period`` set the number of periods to 3.

For Incomes:

- Go to ``Accounting > Reporting > My Incomes`` (or whatever name you used for
  your report)
- In the filter options select:

  - Date: Last Financial Year
  - Comparison: Previous Period and set the number of periods to 3.

If your user is in "Holding Company" as the current company, select in the
filters both companies, else use just "Your Company" in the filter.

Following the IAS 21 the expected values for the reports in the
presentation currency (EUR):

- For Assets:

.. image:: static/description/img-shot-05.png

- For Incomes:

.. image:: static/description/img-shot-06.png

These are their counterparts in the functional currency of the
Consolidated Company (USD).

- For Assets:

.. image:: static/description/img-shot-07.png

- For Incomes:

.. image:: static/description/img-shot-08.png

------

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.vauxoo.com/runbot/133/11.0

Contributors
------------

* Humberto Arocha <hbto@vauxoo.com>
* Erick Birbe <erick@vauxoo.com>
* Edilianny Sanchez <esanchez@vauxoo.com>

Maintainer
----------

.. image:: https://www.vauxoo.com/logo.png
   :alt: Vauxoo
   :target: https://vauxoo.com

This module is maintained by Vauxoo.

a latinamerican company that provides training, coaching,
development and implementation of enterprise management
sytems and bases its entire operation strategy in the use
of Open Source Software and its main product is odoo.

To contribute to this module, please visit http://www.vauxoo.com.
