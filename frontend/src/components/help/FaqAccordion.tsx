import ReactMarkdown from 'react-markdown';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { ThumbsUp, ThumbsDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { FaqArticle } from '@/types/help';

interface FaqAccordionProps {
  articles: FaqArticle[];
  showFeedback?: boolean;
  onFeedback?: (articleId: string, helpful: boolean) => void;
}

export const FaqAccordion = ({ articles, showFeedback = false, onFeedback }: FaqAccordionProps) => {
  return (
    <Accordion type="single" collapsible className="w-full">
      {articles.map((article) => (
        <AccordionItem key={article.id} value={article.id}>
          <AccordionTrigger className="text-left">
            <div className="flex-1">
              <h3 className="font-medium">{article.question}</h3>
              <div className="flex gap-2 mt-1">
                <span className="text-xs text-muted-foreground">{article.category_name}</span>
                <span className="text-xs text-muted-foreground">·</span>
                <span className="text-xs text-muted-foreground">{article.view_count} views</span>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{article.answer}</ReactMarkdown>
            </div>

            {article.keywords.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4">
                {article.keywords.map((keyword, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center rounded-full bg-muted px-2 py-1 text-xs font-medium"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            )}

            {showFeedback && onFeedback && (
              <div className="flex items-center gap-2 mt-4 pt-4 border-t">
                <span className="text-sm text-muted-foreground">Was this helpful?</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onFeedback(article.id, true)}
                  className="h-8"
                >
                  <ThumbsUp className="h-4 w-4 mr-1" />
                  Yes
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onFeedback(article.id, false)}
                  className="h-8"
                >
                  <ThumbsDown className="h-4 w-4 mr-1" />
                  No
                </Button>
              </div>
            )}
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
};
