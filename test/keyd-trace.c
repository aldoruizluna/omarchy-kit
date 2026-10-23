/* test/keyd-trace.c: feed key events to a keyd configuration and print the key events keyd would emit. Used by test_keyd.py.
 *
 * It is a thin driver over keyd's own engine (the same one the daemon runs), so a test can check what a configuration really does
 * without root, a keyboard or the daemon. It needs a keyd source tree (KEYD_SRC), which is not part of this repository:
 *
 *   gcc -DDATA_DIR='""' -DKEYD_H='"<src>/src/keyd.h"' -o keyd-trace keyd-trace.c <src>/src/{keyboard,string,macro,config,log,ini,keys,unicode}.c
 *   keyd-trace CONFIG < events
 *
 * Input, one per line (the key names are keyd's `keyd list-keys` primary names, e.g. "[", "`", "enter"; `control`, `shift`, `meta` and
 * `alt` mean the left key):   KEY down | KEY up | 50ms (time passes) | bind <expression> (what `keyd bind` sends) | # comment
 * A blank line ends a batch: the events so far are processed and keyd's output is printed, then a blank line.
 * Licence note: this file is ours (MIT, like the kit); keyd (MIT) is only compiled against, never copied here.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include KEYD_H

#define MAX_EVENTS 1024
static struct key_event out[MAX_EVENTS];
static size_t nout;

static void send_key(uint8_t code, uint8_t pressed) { out[nout].code = code; out[nout].pressed = pressed; nout++; }
static void on_layer_change(const struct keyboard *k, const struct layer *l, uint8_t active) { (void)k; (void)l; (void)active; }

static uint8_t lookup(const char *n)
{
	if (!strcmp(n, "control")) return KEYD_LEFTCTRL;
	if (!strcmp(n, "shift")) return KEYD_LEFTSHIFT;
	if (!strcmp(n, "meta")) return KEYD_LEFTMETA;
	if (!strcmp(n, "alt")) return KEYD_LEFTALT;
	for (size_t i = 0; i < ARRAY_SIZE(keycode_table); i++)
		if (keycode_table[i].name && !strcmp(keycode_table[i].name, n))
			return i;
	return 0;
}

static void flush(struct keyboard *kbd, struct key_event *in, size_t *n)
{
	if (!*n) return;
	nout = 0;
	kbd_process_events(kbd, in, *n);
	for (size_t i = 0; i < nout; i++)
		printf("%s %s\n", keycode_table[out[i].code].name, out[i].pressed ? "down" : "up");
	printf("\n");
	*n = 0;
}

int main(int argc, char **argv)
{
	struct config cfg;
	struct output o = { .send_key = send_key, .on_layer_change = on_layer_change };
	static struct key_event in[MAX_EVENTS];
	size_t n = 0;
	int t = 0;
	char line[512];

	if (argc != 2) { fprintf(stderr, "usage: keyd-trace CONFIG < events\n"); return 2; }
	if (config_parse(&cfg, argv[1])) { fprintf(stderr, "failed to parse %s\n", argv[1]); return 3; }
	struct keyboard *kbd = new_keyboard(&cfg, &o);

	for (;;) {
		char *r = fgets(line, sizeof line, stdin);
		if (r) line[strcspn(line, "\n")] = 0;
		if (!r || !line[0]) {
			flush(kbd, in, &n);
			if (!r) break;
			continue;
		}
		if (line[0] == '#') continue;
		if (!strncmp(line, "bind ", 5)) {
			flush(kbd, in, &n);
			if (kbd_eval(kbd, line + 5)) printf("BIND FAILED: %s\n", line + 5);
			continue;
		}
		size_t len = strlen(line);
		if (len >= 2 && line[len - 1] == 's' && line[len - 2] == 'm') { t += atoi(line); continue; }
		char *k = strtok(line, " ");
		char *v = strtok(NULL, " \n");
		if (!v || (strcmp(v, "up") && strcmp(v, "down"))) { fprintf(stderr, "bad line: %s\n", line); return 4; }
		uint8_t code = lookup(k);
		if (!code) { fprintf(stderr, "bad key: %s\n", k); return 4; }
		if (n >= MAX_EVENTS) { fprintf(stderr, "too many events\n"); return 4; }
		in[n].code = code;
		in[n].pressed = !strcmp(v, "down");
		in[n].timestamp = t;
		n++;
	}
	return 0;
}
