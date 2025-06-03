.PHONY: help

# Define colors for the banner
BLUE := \033[34m
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
MAGENTA := \033[35m
RESET := \033[0m
BOLD := \033[1m

help:
	@echo ""
	@echo "$(BLUE)$(BOLD)██╗   ██╗ ██████╗ ██╗  ██╗ ██████╗ ██╗      ██████╗  ██████╗ ██╗   ██╗$(RESET)"
	@echo "$(BLUE)$(BOLD)██║   ██║██╔═══██╗╚██╗██╔╝██╔═══██╗██║     ██╔═══██╗██╔════╝ ╚██╗ ██╔╝$(RESET)"
	@echo "$(BLUE)$(BOLD)██║   ██║██║   ██║ ╚███╔╝ ██║   ██║██║     ██║   ██║██║  ███╗ ╚████╔╝ $(RESET)"
	@echo "$(BLUE)$(BOLD)╚██╗ ██╔╝██║   ██║ ██╔██╗ ██║   ██║██║     ██║   ██║██║   ██║  ╚██╔╝  $(RESET)"
	@echo "$(BLUE)$(BOLD) ╚████╔╝ ╚██████╔╝██╔╝ ██╗╚██████╔╝███████╗╚██████╔╝╚██████╔╝   ██║   $(RESET)"
	@echo "$(BLUE)$(BOLD)  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   $(RESET)"
	@echo ""
	@echo "$(GREEN)$(BOLD) ██████╗ █████╗ ████████╗ █████╗ ██╗      ██████╗  ██████╗ $(RESET)"
	@echo "$(GREEN)$(BOLD)██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██║     ██╔═══██╗██╔════╝ $(RESET)"
	@echo "$(GREEN)$(BOLD)██║     ███████║   ██║   ███████║██║     ██║   ██║██║  ███╗$(RESET)"
	@echo "$(GREEN)$(BOLD)██║     ██╔══██║   ██║   ██╔══██║██║     ██║   ██║██║   ██║$(RESET)"
	@echo "$(GREEN)$(BOLD)╚██████╗██║  ██║   ██║   ██║  ██║███████╗╚██████╔╝╚██████╔╝$(RESET)"
	@echo "$(GREEN)$(BOLD) ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ $(RESET)"
	@echo ""
	@echo "$(MAGENTA)$(BOLD)                      Voxology Catalog - CLI Commands$(RESET)"
	@echo "$(BOLD)===============================================================================$(RESET)"
	@echo ""
	@echo "$(CYAN)COMMAND$(RESET)               $(GREEN)DESCRIPTION$(RESET)"
	@echo "-------------------------------------------------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

#====================================================================================================
# Complete Workflow
#====================================================================================================
all: ## Run complete workflow: episodes -> download -> transcribe -> series -> stats
	python get_episode_links.py
	python get_episode_audio_links.py
	python get_audio_files.py
	python transcribe-assemblyai.py
	python parse_series.py
	python stats.py

#====================================================================================================
# Individual Commands
#====================================================================================================
episodes: ## Scrape episode links/metadata and extract audio links
	python get_episode_links.py
	python get_episode_audio_links.py

download: ## Download audio files to catalog directory
	python get_audio_files.py

transcribe: ## Transcribe audio files using AssemblyAI with speaker diarization
	python transcribe-assemblyai.py

stats: ## Generate statistics about audio files (duration, size, transcriptions)
	python stats.py

series: ## Analyze transcriptions to identify podcast series using Gemini AI
	python parse_series.py
