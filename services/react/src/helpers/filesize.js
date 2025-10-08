function formatBytes(bytes, decimals = 2) {
    // Handle cases where bytes is null, undefined, or 0
    if (bytes === null || bytes === undefined) {
      return 'N/A';
    }
    if (!+bytes) {
      return '0 Bytes';
    }
  
    const base = 1024; // Use 1000 for SI units (KB, MB, GB) or 1024 for binary units (KiB, MiB, GiB)
    const dm = decimals < 0 ? 0 : decimals; // Ensure decimals is not negative
    const units = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']; // Add more units as needed
  
    // Calculate the appropriate unit index using logarithm
    const unitIndex = Math.floor(Math.log(bytes) / Math.log(base));
  
    // Calculate the formatted size and round it to the specified decimal places
    const formattedSize = (bytes / Math.pow(base, unitIndex)).toFixed(dm);
  
    // Return the formatted string with the unit
    return `${parseFloat(formattedSize)} ${units[unitIndex]}`;
  }
  
  // Example Usage:
//   console.log(formatBytes(500));        // Output: 500 Bytes
//   console.log(formatBytes(1500));       // Output: 1.46 KB
//   console.log(formatBytes(1500000));    // Output: 1.43 MB
//   console.log(formatBytes(1500000000)); // Output: 1.40 GB
//   console.log(formatBytes(0));          // Output: 0 Bytes
//   console.log(formatBytes(null));       // Output: N/A

  export default formatBytes