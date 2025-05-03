run:
	mkdir -p /tmp/montagem
	python3 fuse_main.py data/secure_files /tmp/montagem


# Diretórios dos arquivos seguros
SECURE_FILES_DIR = /tmp/montagem
CONFIDENTIAL_DIR = $(SECURE_FILES_DIR)/confidential
SECRET_DIR = $(SECURE_FILES_DIR)/secret
TOP_SECRET_DIR = $(SECURE_FILES_DIR)/top_secret
UNCLASSIFIED_DIR = $(SECURE_FILES_DIR)/unclassified

# Arquivos em cada nível de classificação
CONFIDENTIAL_FILES = $(wildcard $(CONFIDENTIAL_DIR)/*)
SECRET_FILES = $(wildcard $(SECRET_DIR)/*)
TOP_SECRET_FILES = $(wildcard $(TOP_SECRET_DIR)/*)
UNCLASSIFIED_FILES = $(wildcard $(UNCLASSIFIED_DIR)/*)



test:
	@echo "Testando acesso aos arquivos..."
	@echo "Arquivos CONFIDENTIAL:"
	@for file in $(CONFIDENTIAL_FILES); do \
		echo "- Acesso aos arquivos: $$file"; \
	done
	@echo "Arquivos SECRET:"
	@for file in $(SECRET_FILES); do \
		echo "- Acesso aos arquivos: $$file "; \
	done
	@echo "Arquivos TOP_SECRET:"
	@for file in $(TOP_SECRET_FILES); do \
		echo "- Acesso aos arquivos: $$file"; \
	done
	@echo "Arquivos UNCLASSIFIED:"
	@for file in $(UNCLASSIFIED_DIR)/*; do \
		echo "- Acesso aos arquivos: $$file"; \
	done