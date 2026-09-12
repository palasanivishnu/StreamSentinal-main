export function normalizeRiskScore(score: unknown): number {
  const num = Number(score);
  if (!Number.isFinite(num)) {
    return 0;
  }
  return num >= 0 && num <= 1 ? num * 100 : num;
}

export function formatUserId(userId?: string): string {
  if (!userId) return '•••• 0000';
  const clean = userId.replace(/^(mock_user_|user_)/i, '');
  if (clean.length >= 4) {
    return `•••• ${clean.slice(-4)}`;
  }
  return `•••• ${clean.padStart(4, '0')}`;
}

export function formatTxnId(txnId?: string): string {
  if (!txnId) return 'TXN-00000000';
  if (txnId.startsWith('TXN-')) return txnId.toUpperCase();
  return `TXN-${txnId.slice(0, 8).toUpperCase()}`;
}

export function formatMerchantName(merchant?: string, category?: string): string {
  if (merchant && merchant !== 'Unknown' && !merchant.startsWith('m')) {
    return merchant;
  }
  const cat = (category || '').toLowerCase();
  if (cat.includes('gas')) return 'Shell Gas Station';
  if (cat.includes('groc') || cat.includes('super')) return 'Walmart Supercenter';
  if (cat.includes('enter') || cat.includes('stream')) return 'Netflix Subscription';
  if (cat.includes('elec') || cat.includes('tech')) return 'Apple Store';
  if (cat.includes('food') || cat.includes('din') || cat.includes('rest')) return 'Starbucks Coffee';
  if (cat.includes('shop') || cat.includes('net') || cat.includes('onl')) return 'Amazon Marketplace';
  return 'Target Retail';
}

export function getCategoryBadgeInfo(category?: string): { emoji: string; label: string } {
  const cat = (category || '').toLowerCase();
  if (cat.includes('gas')) return { emoji: '⛽', label: 'Gas Station' };
  if (cat.includes('groc')) return { emoji: '🛒', label: 'Grocery' };
  if (cat.includes('enter')) return { emoji: '🎬', label: 'Entertainment' };
  if (cat.includes('elec')) return { emoji: '💻', label: 'Electronics' };
  if (cat.includes('food') || cat.includes('din')) return { emoji: '🍔', label: 'Food & Dining' };
  if (cat.includes('shop') || cat.includes('net')) return { emoji: '🛍️', label: 'Online Retail' };
  return { emoji: '💳', label: 'General Retail' };
}
