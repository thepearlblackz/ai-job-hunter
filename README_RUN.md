# Daily Runner

Run the full pipeline manually with:

```bash
python scheduler/daily_runner.py
```

The runner executes the workflow in this order:

1. Search jobs
2. Clean jobs
3. Match jobs
4. Final filter
5. Generate Telegram messages

It prints progress for each stage and stops immediately if any step fails.
