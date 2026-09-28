CC      ?= gcc
AR      ?= ar
CFLAGS  ?= -Wall -Wextra -O2 -std=c11

CORE_DIR    := core
BUILD_DIR   := build
OBJ_DIR     := $(BUILD_DIR)/obj
LIB_DIR     := $(BUILD_DIR)/lib
INCLUDE_DIR := $(BUILD_DIR)/include

LIB_NAME := libfvm.a
LIB      := $(LIB_DIR)/$(LIB_NAME)

SRCS    := $(wildcard $(CORE_DIR)/*.c)
OBJS    := $(patsubst $(CORE_DIR)/%.c,$(OBJ_DIR)/%.o,$(SRCS))
HEADERS := $(wildcard $(CORE_DIR)/*.h)


PREFIX          ?= /usr/local
DESTDIR         ?=
INSTALL_LIB_DIR := $(DESTDIR)$(PREFIX)/lib
INSTALL_INC_DIR := $(DESTDIR)$(PREFIX)/include

.PHONY: all lib headers clean install uninstall

all: lib headers

lib: $(LIB)

$(LIB): $(OBJS) | $(LIB_DIR)
	$(AR) rcs $@ $(OBJS)

$(OBJ_DIR)/%.o: $(CORE_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I$(CORE_DIR) -c $< -o $@


headers: $(HEADERS) | $(INCLUDE_DIR)
	cp $(HEADERS) $(INCLUDE_DIR)/

$(OBJ_DIR) $(LIB_DIR) $(INCLUDE_DIR):
	mkdir -p $@


install: all
	install -d $(INSTALL_LIB_DIR) $(INSTALL_INC_DIR)
	install -m 644 $(LIB) $(INSTALL_LIB_DIR)/
	install -m 644 $(HEADERS) $(INSTALL_INC_DIR)/

uninstall:
	rm -f $(INSTALL_LIB_DIR)/$(LIB_NAME)
	rm -f $(addprefix $(INSTALL_INC_DIR)/,$(notdir $(HEADERS)))

clean:
	rm -rf $(BUILD_DIR)
