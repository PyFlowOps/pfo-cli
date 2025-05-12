# NOTE: make help uses a special comment format to group targets.
# If you'd like your target to show up use the following:
#
# my_target: ##@category_name sample description for my_target
default: help

.PHONY: install	setup clean help

############# Development Section #############
install: ##@meta Installs needed prerequisites and software to develop the project
	$(info ********** Installing Developer Tooling Prerequisites **********)
	@bash -l scripts/install.sh -a
	@bash -l scripts/install.sh -p
	@bash -l -c "dev/.python/bin/python -m pip install --upgrade pip"
	@bash -l -c "dev/.python/bin/python -m pip install -r requirements.txt"
	@asdf reshim
	@echo "[INFO] - Installation Complete!"
	@echo "[INFO] - You can now install the Cookie Cutter templates to your machine..."
	@echo "" 

setup: ##@meta Sets up the project
	$(info ********** Setting up ${service_title} **********)
	@bash -l "scripts/set-env.sh"
	@echo "[INFO] - Project setup complete!"

clean: ##@meta Cleans the project
	$(info ********** Cleaning ${service_title} **********)
	@rm -rf ./dev
	@rm -rf .pytest_cache
	@if [ -d ${HOME}/Library/Caches/pypoetry/virtualenvs ]; then rm -rf ${HOME}/Library/Caches/pypoetry/virtualenvs/${service}-*; fi

help: ##@misc Show this help.
	@echo $(MAKEFILE_LIST)
	@perl -e '$(HELP_FUNC)' $(MAKEFILE_LIST)

# helper function for printing target annotations
# ripped from https://gist.github.com/prwhite/8168133
HELP_FUNC = \
	%help; \
	while(<>) { \
		if(/^([a-z0-9_-]+):.*\#\#(?:@(\w+))?\s(.*)$$/) { \
			push(@{$$help{$$2}}, [$$1, $$3]); \
		} \
	}; \
	print "usage: make [target]\n\n"; \
	for ( sort keys %help ) { \
		print "$$_:\n"; \
		printf("  %-20s %s\n", $$_->[0], $$_->[1]) for @{$$help{$$_}}; \
		print "\n"; \
	}
