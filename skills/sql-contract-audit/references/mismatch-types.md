# Mismatch Types

- `implementation gap`: mapping/playbook expect a field, SQL does not output it
- `doc drift`: SQL and mapping agree, playbook still says something else
- `contract drift`: mapping and SQL disagree on names/order/meaning
- `sample/runtime drift`: checked-in contract looks correct, produced sample does not match it
