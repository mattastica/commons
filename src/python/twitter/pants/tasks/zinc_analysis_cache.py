# ==================================================================================================
# Copyright 2011 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

__author__ = 'Mark C. Chu-Carroll'

from collections import defaultdict


class ZincMergedAnalysisCache(object):
  """
  A wrapper for zinc analysis caches.

  This contains the information from a collection of Zinc analysis caches, merged together,
  for use in dependency analysis.
  """
  def __init__(self, generated, upstream):
    """
    Parameters:
      generated: the set of pathnames of analysis caches generated by the latest zinc run.
      upstream: the set of pathnames of upstream analysis caches used by the latest zinc run.
    """
    self.caches = generated.union(upstream)
    # Map from scala source files to the class files generated from that source
    self.products = defaultdict(set)
    # Map from scala sources to jar files they depend on. (And, rarely, class files.)
    self.binary_deps = defaultdict(set)
    # Map from scala sources to the source files providing the classes that they depend on
    # The set of source files here does *not* appear to include inheritance!
    # eg, in src/jvm/com/foursquare/api/util/BUILD:util,
    # in the source file ClientMetrics, class ClientView extends PrettyEnumeration, but
    # the file declaring PrettyEnumeration is *not* in the source deps.
    # But PrettyEnumeration *is* included in the list of classes in external_deps.
    self.source_deps = defaultdict(set)
    # Map from scala sources to the classes that they depend on. (Not class files, source files, but just classes.
    self.external_deps = defaultdict(set)
    # Map from scala sources to the classes that they provide. (Again, not class files, fully-qualified class names.)
    self.class_names = defaultdict(set)
    for c in self.caches:
      self.parse(c)

  def parse(self, cachepath):
    zincfile = "%s.relations" % cachepath
    try:
      zincfile = open(zincfile, "r")
    except IOError:
      print "Warning: analysis cache file %s not found" % cachepath
      return
    mode = None
    for line in zincfile:
      if line.startswith("products:"):
        mode = "products"
      elif line.startswith("binary dependencies:"):
        mode = "binary"
      elif line.startswith("source dependencies:"):
        mode = "source"
      elif line.startswith("external dependencies:"):
        mode = "external"
      elif line.startswith("class names:"):
        mode = "class"
      else:
        (src, sep, dep) = line.partition("->")
        src = src.strip()
        dep = dep.strip()
        if sep == "" and line != "\n":
            print ("Syntax error: line is neither a modeline nor a dep. '%s'"  %
                    line)
            continue
        if mode == "products":
          self.products[src].add(dep)
        elif mode == "binary":
          self.binary_deps[src].add(dep)
        elif mode == "source":
          self.source_deps[src].add(dep)
        elif mode == "external":
          self.external_deps[src].add(dep)
        elif mode == "class":
          self.class_names[src].add(dep)
        else:
          print "Unprocessed line, mode = %s" % mode

