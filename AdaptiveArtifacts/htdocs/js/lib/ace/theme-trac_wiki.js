/* ***** BEGIN LICENSE BLOCK *****
 * Distributed under the BSD license:
 *
 * Copyright (c) 2010, Ajax.org B.V.
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in the
 *       documentation and/or other materials provided with the distribution.
 *     * Neither the name of Ajax.org B.V. nor the
 *       names of its contributors may be used to endorse or promote products
 *       derived from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL AJAX.ORG B.V. BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * ***** END LICENSE BLOCK ***** */

define('ace/theme/trac_wiki', ['require', 'exports', 'module', 'ace/lib/dom'], function(require, exports, module) {

exports.isDark = false;
exports.cssClass = "ace-trac-wiki";
exports.cssText = "/* CSS style content from github's default pygments highlighter template.\
   Cursor and selection styles from textmate.css. */\
.ace-trac-wiki {\
  padding: 6px 10px;\
  position: relative;\
  border: 1px solid #D7D7D7;\
  border-radius: 0.3em 0.3em 0.3em 0.3em;\
  background-color: white;\
  vertical-align: text-bottom;\
  padding: 0;\
  width: 100%;\
  min-height: 12em;\
}\
\
.ace_editor {\
  font-size: 10px;\
}\
\
.ace-trac-wiki .ace_gutter {\
  background: #e8e8e8;\
  color: #AAA;\
}\
\
.ace-trac-wiki .ace_scroller {\
  background: #fff;\
}\
\
.ace-trac-wiki .ace_keyword {\
    border-bottom: 1px dashed blue;\
    color: blue;\
}\
\
.ace-trac-wiki .ace_string {\
  color: #D14;\
}\
\
.ace-trac-wiki .ace_variable.ace_class {\
  color: teal;\
}\
\
.ace-trac-wiki .ace_constant.ace_numeric {\
  color: #099;\
}\
\
.ace-trac-wiki .ace_constant.ace_buildin {\
  color: #0086B3;\
}\
\
.ace-trac-wiki .ace_support.ace_function {\
  color: #0086B3;\
}\
\
.ace-trac-wiki .ace_comment {\
  color: #998;\
  font-style: italic;\
}\
\
.ace-trac-wiki .ace_variable.ace_language  {\
  color: #0086B3;\
}\
\
.ace-trac-wiki .ace_paren {\
  font-weight: bold;\
}\
\
.ace-trac-wiki .ace_boolean {\
  font-weight: bold;\
}\
\
.ace-trac-wiki .ace_string.ace_regexp {\
  color: #009926;\
  font-weight: normal;\
}\
\
.ace-trac-wiki .ace_variable.ace_instancce {\
  color: teal;\
}\
\
.ace-trac-wiki .ace_constant.ace_language {\
  font-weight: bold;\
}\
\
.ace-trac-wiki .ace_text-layer {\
}\
\
.ace-trac-wiki .ace_cursor {\
  border-left: 2px solid black !important;\
}\
\
.ace-trac-wiki .ace_cursor.ace_overwrite {\
  border-left: 0px;\
  border-bottom: 1px solid black;\
}\
\
.ace-trac-wiki .ace_marker-layer .ace_active_line {\
  background: rgb(255, 255, 204);\
}\
.ace-trac-wiki .ace_marker-layer .ace_selection {\
  background: rgb(181, 213, 255);\
}\
.ace-trac-wiki.multiselect .ace_selection.start {\
  box-shadow: 0 0 3px 0px white;\
  border-radius: 2px;\
}\
/* bold keywords cause cursor issues for some fonts */\
/* this disables bold style for editor and keeps for static highlighter */\
.ace-trac-wiki.ace_editor .ace_line > span {\
    font-weight: normal !important;\
}\
\
.ace-trac-wiki .ace_marker-layer .ace_step {\
  background: rgb(252, 255, 0);\
}\
\
.ace-trac-wiki .ace_marker-layer .ace_stack {\
  background: rgb(164, 229, 101);\
}\
\
.ace-trac-wiki .ace_marker-layer .ace_bracket {\
  margin: -1px 0 0 -1px;\
  border: 1px solid rgb(192, 192, 192);\
}\
\
.ace-trac-wiki .ace_gutter_active_line {\
    background-color : rgba(0, 0, 0, 0.07);\
}\
\
.ace-trac-wiki .ace_marker-layer .ace_selected_word {\
  background: rgb(250, 250, 255);\
  border: 1px solid rgb(200, 200, 250);\
\
}\
\
.ace-trac-wiki .ace_print_margin {\
  width: 1px;\
  background: #e8e8e8;\
}\
\
.ace-trac-wiki .ace_indent-guide {\
  background: url(\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAE0lEQVQImWP4////f4bLly//BwAmVgd1/w11/gAAAABJRU5ErkJggg==\") right repeat-y;\
}";

    var dom = require("../lib/dom");
    dom.importCssString(exports.cssText, exports.cssClass);
});
