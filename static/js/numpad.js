/**
 * A simple numpad that only uses DOM-JavaScript to avoid all that jQuery bloat.
 * 
 * ----------------------------------------------------------------------------
 * "THE BEER-WARE LICENSE" (Revision 42):
 * <br _at_ re-web _dot_ eu> wrote this file.  
 * As long as you retain this notice you can do whatever you want with this 
 * stuff. If we meet some day, and you think this stuff is worth it, you can
 * buy me a beer in return.                             Balthasar Reuter, 2015.
 * ----------------------------------------------------------------------------
 */


/**
 * Determines the id of the input field the numpad works on.
 */
function numpadGetElement() {
  return document.getElementById("numpad_element_id").value;
}

/**
 * Sets the id of the input field the numpad works on.
 */
function numpadSetElement(element_id) {
  document.getElementById("numpad_element_id").value = element_id;
}

/**
 * Lets the keypad appear.
 */
function numpadShow(element_id) {
  var element_rect = document.getElementById(element_id).getBoundingClientRect();
  var numpad = document.getElementById("numpad");
  numpad.style.position = "absolute";
  numpad.style.top = element_rect.bottom + 'px';
  numpad.style.left = element_rect.left + 'px';
  numpad.style.visibility = 'visible';
  numpadSetElement(element_id);
}

/**
 * Lets the keypad disappear.
 */
function numpadHide() {
  document.getElementById("numpad").style.visibility = 'hidden';
  numpadSetElement("");
}

/**
 * Takes the given text and converts it into format XXX.XX.
 * In this course it ignores any previously existing dots.
 */
function numpadShiftComma(text, element_id) {
  text = "000" + text;
  var text_wo_dot = text.replace(".", "");
  var full_text = parseInt(text_wo_dot.substring(0, (text_wo_dot.length - 2))) 
                  + "." + text_wo_dot.substring(text_wo_dot.length - 2);
  document.getElementById(element_id).value = full_text;
}

/**
 * Takes the existing value from the given element and appends the 
 * given text.
 */
function numpadAppend(text) {
  var element_id = numpadGetElement();
  numpadShiftComma( document.getElementById(element_id).value + text, element_id );
}

/**
 * Deletes the last character from the given element
 */
function numpadBackspace() {
  var element_id = numpadGetElement();
  var val = document.getElementById(element_id).value;
  numpadShiftComma( val.substring(0, val.length - 1), element_id );
}

/**
 * Clears the content of the field
 */
function numpadClear() {
  numpadShiftComma( "", numpadGetElement() );
}
