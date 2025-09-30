
function formatFullDate(iso?: string): string {
  if (!iso) return "No date";
  const parts = iso.split("-");
  if (parts.length !== 3) return iso; // leave unknown format
  const [yStr, mStr, dStr] = parts;
  const y = Number(yStr);
  const m = Number(mStr);
  const d = Number(dStr);
  if (!y || !m || !d) return iso;

  const monthNames = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
  ];
  const month = monthNames[m - 1] ?? mStr;

  const ordinal = (n: number) => {
    const rem10 = n % 10;
    const rem100 = n % 100;
    if (rem10 === 1 && rem100 !== 11) return `${n}st`;
    if (rem10 === 2 && rem100 !== 12) return `${n}nd`;
    if (rem10 === 3 && rem100 !== 13) return `${n}rd`;
    return `${n}th`;
  };

  return `${month} ${ordinal(d)}, ${y}`;
}

export default formatFullDate;