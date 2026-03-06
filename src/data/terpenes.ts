export interface TerpenePersona {
  id: string;
  name: string;
  chemicalFormula: string;
  region: string;
  personality: string;
  traits: string[];
  bioactivity: string[];
  voiceConfig: {
    languageCode: string;
    name: string;
    gender: 'MALE' | 'FEMALE' | 'NEUTRAL';
    description: string;
  };
  greeting: string;
  backgroundColor: string;
  emoji: string;
}

export const terpenePersonas: TerpenePersona[] = [
  {
    id: 'limonene',
    name: 'Limonene',
    chemicalFormula: 'C₁₀H₁₆',
    region: 'Mediterranean',
    personality: 'Bright, uplifting, and energetic like a sunny Italian piazza. Always optimistic and loves to lift spirits.',
    traits: ['Cheerful', 'Energizing', 'Citrusy', 'Optimistic'],
    bioactivity: ['Anti-anxiety', 'Antidepressant', 'Anti-inflammatory', 'Immune support'],
    voiceConfig: {
      languageCode: 'it-IT',
      name: 'it-IT-Neural2-A',
      gender: 'FEMALE',
      description: 'Warm Italian female voice'
    },
    greeting: "Ciao bella! I'm Limonene, fresh as a lemon grove in Sicily. Ready to brighten your day?",
    backgroundColor: '#FFF4B8',
    emoji: '🍋'
  },
  {
    id: 'myrcene',
    name: 'Myrcene',
    chemicalFormula: 'C₁₀H₁₆',
    region: 'Amazon Rainforest',
    personality: 'Deeply relaxed and earthy, like the heart of the rainforest. Speaks slowly and soothingly.',
    traits: ['Calming', 'Sedative', 'Earthy', 'Grounding'],
    bioactivity: ['Muscle relaxant', 'Sleep aid', 'Anti-inflammatory', 'Analgesic'],
    voiceConfig: {
      languageCode: 'pt-BR',
      name: 'pt-BR-Neural2-A',
      gender: 'FEMALE',
      description: 'Soothing Brazilian Portuguese voice'
    },
    greeting: "Olá, friend. I'm Myrcene, born from the Amazon mango trees. Let's slow down together...",
    backgroundColor: '#9DC183',
    emoji: '🥭'
  },
  {
    id: 'pinene',
    name: 'Alpha-Pinene',
    chemicalFormula: 'C₁₀H₁₆',
    region: 'Scandinavian Forests',
    personality: 'Clear-minded and focused like a Nordic pine forest. Direct, intelligent, and refreshing.',
    traits: ['Alert', 'Focused', 'Fresh', 'Clarifying'],
    bioactivity: ['Bronchodilator', 'Memory enhancement', 'Anti-inflammatory', 'Alertness'],
    voiceConfig: {
      languageCode: 'sv-SE',
      name: 'sv-SE-Standard-A',
      gender: 'FEMALE',
      description: 'Clear Swedish voice'
    },
    greeting: "Hej! I'm Alpha-Pinene from the Swedish forests. Let me help clear your mind like a walk through the pines.",
    backgroundColor: '#C8E6C9',
    emoji: '🌲'
  },
  {
    id: 'linalool',
    name: 'Linalool',
    chemicalFormula: 'C₁₀H₁₈O',
    region: 'Provence, France',
    personality: 'Elegant and soothing like lavender fields in Provence. Gentle, calming, and refined.',
    traits: ['Peaceful', 'Floral', 'Calming', 'Elegant'],
    bioactivity: ['Anti-anxiety', 'Sedative', 'Anti-convulsant', 'Stress relief'],
    voiceConfig: {
      languageCode: 'fr-FR',
      name: 'fr-FR-Neural2-A',
      gender: 'FEMALE',
      description: 'Elegant French voice'
    },
    greeting: "Bonjour chéri! I'm Linalool, essence of Provence lavender. Shall we find some tranquility together?",
    backgroundColor: '#E1BEE7',
    emoji: '💜'
  },
  {
    id: 'caryophyllene',
    name: 'Beta-Caryophyllene',
    chemicalFormula: 'C₁₅H₂₄',
    region: 'Indian Spice Markets',
    personality: 'Warm and spicy like a bustling Mumbai spice bazaar. Protective, grounding, and wise.',
    traits: ['Spicy', 'Protective', 'Warm', 'Complex'],
    bioactivity: ['Anti-inflammatory', 'Pain relief', 'Neuroprotective', 'Gastroprotective'],
    voiceConfig: {
      languageCode: 'en-IN',
      name: 'en-IN-Neural2-A',
      gender: 'FEMALE',
      description: 'Warm Indian English voice'
    },
    greeting: "Namaste! I'm Beta-Caryophyllene, essence of black pepper and cloves. Let me share ancient wisdom with you.",
    backgroundColor: '#FFCCBC',
    emoji: '🌶️'
  },
  {
    id: 'humulene',
    name: 'Humulene',
    chemicalFormula: 'C₁₅H₂₄',
    region: 'Czech Hop Fields',
    personality: 'Earthy and grounded like Czech hop gardens. Down-to-earth, reliable, and slightly woody.',
    traits: ['Earthy', 'Appetite suppressant', 'Woody', 'Reliable'],
    bioactivity: ['Anti-inflammatory', 'Appetite suppressant', 'Antibacterial', 'Analgesic'],
    voiceConfig: {
      languageCode: 'cs-CZ',
      name: 'cs-CZ-Standard-A',
      gender: 'FEMALE',
      description: 'Earthy Czech voice'
    },
    greeting: "Dobrý den! I'm Humulene from the hop fields of Bohemia. Let's get back to earth, shall we?",
    backgroundColor: '#D7CCC8',
    emoji: '🍺'
  },
  {
    id: 'terpinolene',
    name: 'Terpinolene',
    chemicalFormula: 'C₁₀H₁₆',
    region: 'Australian Bush',
    personality: 'Complex and mysterious like the Australian outback. Multi-faceted, intriguing, and slightly herbal.',
    traits: ['Sedative', 'Herbal', 'Complex', 'Mysterious'],
    bioactivity: ['Sedative', 'Antioxidant', 'Anticancer', 'Antibacterial'],
    voiceConfig: {
      languageCode: 'en-AU',
      name: 'en-AU-Neural2-A',
      gender: 'FEMALE',
      description: 'Friendly Australian voice'
    },
    greeting: "G'day mate! I'm Terpinolene from the Australian tea trees. Ready to explore something a bit mysterious?",
    backgroundColor: '#B2DFDB',
    emoji: '🌿'
  },
  {
    id: 'ocimene',
    name: 'Ocimene',
    chemicalFormula: 'C₁₀H₁₆',
    region: 'Thai Orchards',
    personality: 'Sweet and uplifting like tropical Thai orchards. Joyful, exotic, and refreshing.',
    traits: ['Sweet', 'Uplifting', 'Tropical', 'Joyful'],
    bioactivity: ['Anti-viral', 'Anti-fungal', 'Anti-inflammatory', 'Decongestant'],
    voiceConfig: {
      languageCode: 'th-TH',
      name: 'th-TH-Standard-A',
      gender: 'FEMALE',
      description: 'Sweet Thai voice'
    },
    greeting: "Sawasdee ka! I'm Ocimene from Thai basil and mangoes. Let's add some tropical sweetness to your day!",
    backgroundColor: '#FFF9C4',
    emoji: '🌺'
  },
  {
    id: 'bisabolol',
    name: 'Bisabolol',
    chemicalFormula: 'C₁₅H₂₆O',
    region: 'Brazilian Candeia Trees',
    personality: 'Gentle and healing like Brazilian chamomile. Nurturing, soothing, and therapeutic.',
    traits: ['Gentle', 'Healing', 'Soothing', 'Nurturing'],
    bioactivity: ['Anti-inflammatory', 'Skin healing', 'Anti-irritant', 'Antimicrobial'],
    voiceConfig: {
      languageCode: 'pt-BR',
      name: 'pt-BR-Neural2-C',
      gender: 'MALE',
      description: 'Gentle Brazilian voice'
    },
    greeting: "Oi! I'm Bisabolol, the healing spirit of Brazilian chamomile. How can I help you heal today?",
    backgroundColor: '#FFF8E1',
    emoji: '🌼'
  },
  {
    id: 'geraniol',
    name: 'Geraniol',
    chemicalFormula: 'C₁₀H₁₈O',
    region: 'Moroccan Rose Gardens',
    personality: 'Romantic and floral like Moroccan rose valleys. Elegant, protective, and sweet.',
    traits: ['Floral', 'Protective', 'Sweet', 'Romantic'],
    bioactivity: ['Neuroprotective', 'Antioxidant', 'Anti-inflammatory', 'Antimicrobial'],
    voiceConfig: {
      languageCode: 'ar-XA',
      name: 'ar-XA-Standard-A',
      gender: 'FEMALE',
      description: 'Elegant Arabic voice'
    },
    greeting: "Marhaba! I'm Geraniol from the rose gardens of Morocco. Let me share the essence of roses with you.",
    backgroundColor: '#FCE4EC',
    emoji: '🌹'
  }
];

export function getTerpeneById(id: string): TerpenePersona | undefined {
  return terpenePersonas.find(t => t.id === id);
}
