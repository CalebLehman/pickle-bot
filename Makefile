LOCATIONS := pickle_bot tests

help:
	@echo "Makefile help:"
	@echo "  lint - Run linter(s)"
	@echo "  format - Run formater(s)"

lint:
	poetry run flake8 $(LOCATIONS)

format:
	poetry run black $(LOCATIONS)
	find $(LOCALTIONS) -name '*.py' -exec poetry run pyupgrade {} +
