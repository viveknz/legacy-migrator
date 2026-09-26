# Problem & Solution Statement

Every team inherits a database nobody wants to touch. It works, nobody's quite sure why, and touching it feels like defusing something. Migrating it properly usually means someone spending most of a day just reading old stored procedures and triggers to figure out what will actually break, before a single line of the real migration gets written.

That's the problem this project takes on with IBM Bob 2.0, and the goal from the start was to actually solve it, not just describe it nicely. Plenty of tools in this space stop at a good-looking risk report. We didn't want to build another one of those.

So Bug Squash built a Legacy Migration Risk Assistant that audits a legacy database, scores its migration risk with real evidence, and then actually carries out the migration end to end into Postgres. We used Microsoft's own Northwind and Pubs sample databases as the test case, deliberately, because they're genuinely old — 1998-era SQL Server, with real deprecated syntax and business logic buried in procedures and triggers, not a toy example dressed up to look impressive.

Bob audited both databases, generated the Postgres schema, wrote the data-migration script, and ran it. The result: 13 tables, 13 foreign keys, and 3,308 rows moved, with the row counts verified against the source — and verified twice, by wiping the target and re-running it clean, because a claim that only works once isn't a claim worth making.

Why does this matter? Because the teams who'd actually use this need to trust an audit enough to act on it, not just admire it. Turning an 8-hour manual review into a 3-minute automated one, with the exact offending line quoted rather than a vague warning, is the kind of time saving that decides whether a modernization project gets greenlit at all.

Where this stands apart from other entries covering similar ground is the follow-through. It would've been easy to stop at the report. Instead, Bob generated the migration, ran it, and then — in a separate step — verified its own result against the source data. That last part is the whole point: an audit you can trust is only half the job. The other half is proving the fix actually works.
