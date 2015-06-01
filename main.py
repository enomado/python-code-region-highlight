## -*- coding: utf-8 -*-

import ast, random, string, codecs
from StringIO import StringIO

from mako.runtime import Context
from mako.template import Template

from rope.base.project import Project

from rope.base import (change, pyobjects, exceptions, pynames, worder,
                       codeanalyze)

from rope.refactor import patchedast
from rope.refactor.restructure import Restructure
from rope.refactor.importutils import module_imports
from rope.refactor.importutils.importinfo import FromImport
from rope.base.codeanalyze import SourceLinesAdapter, ChangeCollector

from mako.exceptions import RichTraceback
import markupsafe


class Highlight(object):

	lines = None
	node = None
	resource = None

	def print_code_exact(self):
		return self.lines.code[self.node.region[0]:self.node.region[1]]

	def print_code(self):
		region = self.node.region
		lines_min, lines_max = self.lines.get_line_number(region[0]), self.lines.get_line_number(region[1])
		
		lines_min -= 1
		if lines_min < 0:
			lines_min = 0

		lines_max += 2
		if lines_max > self.lines.length():
			lines_max = self.lines.length()

		min_offset = self.lines.get_line_start(lines_min)
		max_offset = self.lines.get_line_end(lines_max)

		code = self.lines.code[min_offset: max_offset]

		region_min = region[0] - min_offset
		region_max = region[1] - min_offset

		orig_offset = self.lines.get_line_start(self.node.lineno) + self.node.col_offset
		orig_offset = orig_offset - min_offset

		orig_f_offset = None
		if hasattr(self.node, 'f_lineno') and hasattr(self.node, 'f_offset'):
			try:
				orig_f_offset = self.lines.get_line_start(self.node.f_lineno) + self.node.f_offset
				orig_f_offset = orig_f_offset - min_offset
			except:
				pass

		rnd = lambda : ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
		a1, a2, a3, a4, a5, a6 = tuple(rnd() for _ in range(6))

		t = {
			a1: u'<span style="background-color:#339999;">',
			a2: u'</span>',
			a3: u'<span style="background-color:#660000;">',
			a4: u'</span>',
			a5: u'<span style="background-color:#060f0f;">',
			a6: u'</span>',
			}

		c = ChangeCollector(code)
		c.add_change(region_min, region_min, a1)
		c.add_change(region_max, region_max, a2)
		c.add_change(orig_offset, orig_offset, a3)
		c.add_change(orig_offset+1, orig_offset+1, a4)

		if orig_f_offset:
			c.add_change(orig_f_offset, orig_f_offset, a5)
			c.add_change(orig_f_offset+1, orig_f_offset+1, a6)

		code = markupsafe.escape(code)

		rend_code = c.get_changed()

		for w, h in t.items():
			rend_code = rend_code.replace(w,h)			

		return rend_code


def translate_to_offset(lines, q):
	offset = lines.get_line_start(q.lineno) + q.col_offset
	return offset


def run(project_directory):
	failures = {}
	count_errors = 0
	project = Project(project_directory)
	files = project.pycore.get_python_files()

	for file_num, resource in enumerate(files):
		if count_errors > 500:
			break
		pymodule = project.pycore.resource_to_pyobject(resource)

		source, node = pymodule.source_code, pymodule.get_ast()

		lines = SourceLinesAdapter(source)

		try:
			patchedast.patch_ast(node, source)
		except Exception as ex:
			print 'warning: can not read {}'.format(resource)
			continue

		for n in ast.walk(node):
			if hasattr(n, 'region') and hasattr(n, 'lineno') and n.region[0]:
				if abs(translate_to_offset(lines, n) - n.region[0]) > 1 :
					count_errors += 1
					fail = Highlight()
					fail.node = n
					fail.lines = lines
					fail.resource = resource

					failures.setdefault(n.__class__, [])
					failures[n.__class__].append(fail)

	return failures
		

def render(failures):
	template = Template(filename='tmpl.mako', output_encoding='utf-8',  input_encoding='utf-8')
	
	instances = []
	for t, vals in failures.iteritems():
		for i, val in enumerate(vals):
			if i > 20:
				break
			instances.append(val)

	buf = codecs.open("results.html", "w", encoding="utf-8")
	ctx = Context(buf, instances = instances)

	try:
		res = template.render_context(ctx)
	except:
		raise
		traceback = RichTraceback()
		for (filename, lineno, function, line) in traceback.traceback:
			pass
			print("File %s, line %s, in %s" % (filename, lineno, function))
			print(line, "\n")
		print("%s: %s" % (str(traceback.error.__class__.__name__), traceback.error))


def main():
	failures = run('/home/sc/t/turnik/.env/lib/python2.7/site-packages')
	render(failures)


if __name__ == "__main__":
    main()