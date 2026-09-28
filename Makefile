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


GENERATED_DIR := generated
PYTHON_DIR    := python
LUA_DIR       := lua

LUA_CFLAGS ?= $(shell pkg-config --cflags lua5.4 2>/dev/null || pkg-config --cflags lua 2>/dev/null)
LUA_LIBS   ?= $(shell pkg-config --libs lua5.4 2>/dev/null || pkg-config --libs lua 2>/dev/null)

PREFIX          ?= /usr/local
DESTDIR         ?=
INSTALL_LIB_DIR := $(DESTDIR)$(PREFIX)/lib
INSTALL_INC_DIR := $(DESTDIR)$(PREFIX)/include

.PHONY: all lib headers clean install uninstall py-modules lua-modules

all: lib headers

lib: $(LIB)

$(LIB): $(OBJS) | $(LIB_DIR)
	$(AR) rcs $@ $(OBJS)

$(OBJ_DIR)/%.o: $(CORE_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I$(CORE_DIR) -c $< -o $@


headers: $(HEADERS) | $(INCLUDE_DIR)
	cp $(HEADERS) $(INCLUDE_DIR)/

$(OBJ_DIR) $(LIB_DIR) $(INCLUDE_DIR) $(PYTHON_DIR) $(LUA_DIR):
	mkdir -p $@



install: all
	install -d $(INSTALL_LIB_DIR) $(INSTALL_INC_DIR)
	install -m 644 $(LIB) $(INSTALL_LIB_DIR)/
	install -m 644 $(HEADERS) $(INSTALL_INC_DIR)/

uninstall:
	rm -f $(INSTALL_LIB_DIR)/$(LIB_NAME)
	rm -f $(addprefix $(INSTALL_INC_DIR)/,$(notdir $(HEADERS)))


CONTROLLER_SRCS := $(filter-out $(GENERATED_DIR)/test_%.c,$(wildcard $(GENERATED_DIR)/*.c))
CONTROLLER_LIBS := $(patsubst $(GENERATED_DIR)/%.c,$(PYTHON_DIR)/lib%.so,$(CONTROLLER_SRCS))

py-modules: $(CONTROLLER_LIBS)

$(PYTHON_DIR)/lib%.so: $(GENERATED_DIR)/%.c $(SRCS) | $(PYTHON_DIR)
	$(CC) $(CFLAGS) -fPIC -shared -I$(CORE_DIR) -I$(GENERATED_DIR) \
		$(SRCS) $< -o $@

# require("name") busca name.so (sin prefijo lib) en package.cpath.
LUA_MODULES := $(patsubst $(GENERATED_DIR)/%.c,$(LUA_DIR)/%.so,$(CONTROLLER_SRCS))

lua-modules: $(LUA_MODULES)

$(LUA_DIR)/%.so: $(GENERATED_DIR)/%.c $(LUA_DIR)/%_lua.c $(SRCS) | $(LUA_DIR)
	$(CC) $(CFLAGS) $(LUA_CFLAGS) -fPIC -shared -I$(CORE_DIR) -I$(GENERATED_DIR) \
		$(SRCS) $< $(LUA_DIR)/$*_lua.c $(LUA_LIBS) -o $@

clean:
	rm -rf $(BUILD_DIR)
