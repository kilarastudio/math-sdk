TEST_NAMES = 0_0_cluster 0_0_scatter 0_0_lines 0_0_expwilds 0_0_ways 0_0_lines_feature_match keris_wild

.PHONY: setup run test test_run clean

setup:
	uv sync


run GAME:
	uv run python games/$(GAME)/run.py
	@echo "Checking compression setting..."
	@if grep -q "compression = False" games/$(GAME)/run.py; then \
		echo "Compression is disabled, formatting books files..."; \
		uv run python utils/format_books_json.py games/$(GAME) || echo "Warning: Failed to format books files"; \
	else \
		echo "Compression is enabled, skipping formatting."; \
	fi

test:
	uv run pytest tests/

test_run:
	@for f in $(TEST_NAMES); do \
		echo "processing $$f"; \
		uv run python games/$$f/run.py; \
	done


clean:
	rm -rf .venv env __pycache__ *.pyc
