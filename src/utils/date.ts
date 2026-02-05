export function formatDistanceToNow(date: Date): string {
  const now = new Date();
  const diff = date.getTime() - now.getTime();
  const minutes = Math.floor(diff / 1000 / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d left`;
  }
  if (hours > 0) {
    return `${hours}h left`;
  }
  if (minutes > 0) {
    return `${minutes}m left`;
  }
  return 'Expired';
}