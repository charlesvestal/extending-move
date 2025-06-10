/* Shared JavaScript functions */

/**
 * Debounce: returns a debounced version of the provided function.
 * @param {Function} func - The function to debounce.
 * @param {number} wait - The number of milliseconds to delay.
 * @returns {Function} - The debounced function.
 */
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}


/**
 * Returns a finer step value for percent controls when within ±10%.
 *
 * @param {number} value - Current numeric value.
 * @param {string} unit - Unit string (e.g. '%').
 * @param {number} baseStep - Default step value.
 * @param {boolean} shouldScale - Whether the value is represented as 0..1.
 * @returns {number} - The adjusted step size.
 */
function getPercentStep(value, unit, baseStep, shouldScale) {
  if (unit === '%') {
    const disp = shouldScale ? value * 100 : value;
    if (Math.abs(disp) < 10) return baseStep / 10;
  }
  return baseStep;
}

/**
 * Computes decimal places for percent controls based on magnitude.
 *
 * @param {number} value - Current numeric value.
 * @param {string} unit - Unit string.
 * @param {number} defaultDecimals - Default decimals to display.
 * @param {boolean} shouldScale - Whether the value is represented as 0..1.
 * @returns {number} - The decimals to use when formatting.
 */
function getPercentDecimals(value, unit, defaultDecimals, shouldScale) {
  if (unit === '%' && Math.abs((shouldScale ? value * 100 : value)) < 10) {
    return 1;
  }
  return defaultDecimals;
}

// expose helpers for non-module scripts
if (typeof window !== 'undefined') {
  window.getPercentStep = getPercentStep;
  window.getPercentDecimals = getPercentDecimals;
}
