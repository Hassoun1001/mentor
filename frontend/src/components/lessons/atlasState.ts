/** Filters and open cards of the Methods Atlas, kept while the reader visits a lesson. */
export type AtlasState = {
  text: string;
  group: string;
  usage: string;
  verdict: string;
  market: string;
  access: string;
  lessonOnly: boolean;
  open: string[];
};

export const EMPTY_ATLAS: AtlasState = {
  text: '',
  group: '',
  usage: '',
  verdict: '',
  market: '',
  access: '',
  lessonOnly: false,
  open: [],
};
