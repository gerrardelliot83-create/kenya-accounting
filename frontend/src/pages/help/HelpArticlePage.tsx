import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { ArrowLeft, Clock, Eye, Tag, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useHelpArticle, useHelpArticles } from '@/hooks/useHelp';

export const HelpArticlePage = () => {
  const { slug } = useParams<{ slug: string }>();

  const { data: article, isLoading, error } = useHelpArticle(slug || '');
  const { data: allArticles } = useHelpArticles();

  // Get related articles (same category, excluding current)
  const relatedArticles =
    allArticles
      ?.filter((a) => a.category === article?.category && a.slug !== slug)
      .slice(0, 3) || [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-1/3" />
        <Card>
          <CardContent className="pt-6 space-y-4">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" asChild>
          <Link to="/help">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Help Centre
          </Link>
        </Button>

        <Alert variant="destructive">
          <AlertDescription>
            Article not found. Please try searching for another article.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Main Content */}
      <div className="lg:col-span-2 space-y-6">
        {/* Back Button */}
        <Button variant="ghost" asChild>
          <Link to="/help">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Help Centre
          </Link>
        </Button>

        {/* Article */}
        <Card>
          <CardHeader>
            <div className="space-y-4">
              <div>
                <Badge variant="secondary" className="mb-2">
                  {article.category}
                </Badge>
                <h1 className="text-3xl font-bold tracking-tight">{article.title}</h1>
              </div>

              {/* Metadata */}
              <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  <span>{article.estimated_read_time} min read</span>
                </div>
                <div className="flex items-center gap-1">
                  <Eye className="h-4 w-4" />
                  <span>{article.view_count} views</span>
                </div>
              </div>

              {/* Tags */}
              {article.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {article.tags.map((tag, idx) => (
                    <Badge key={idx} variant="outline" className="gap-1">
                      <Tag className="h-3 w-3" />
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </CardHeader>

          <Separator />

          <CardContent className="pt-6">
            {/* Article Content */}
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{article.content}</ReactMarkdown>
            </div>

            <Separator className="my-8" />

            {/* Was This Helpful */}
            <div className="flex items-center justify-center gap-4 py-4">
              <span className="text-sm font-medium">Was this article helpful?</span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <ThumbsUp className="h-4 w-4 mr-1" />
                  Yes
                </Button>
                <Button variant="outline" size="sm">
                  <ThumbsDown className="h-4 w-4 mr-1" />
                  No
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Still Need Help */}
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold">Still need help?</h3>
                <p className="text-muted-foreground text-sm mt-1">
                  Contact our support team for personalized assistance
                </p>
              </div>
              <Button asChild>
                <Link to="/help/tickets/new">Create Support Ticket</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sidebar - Related Articles */}
      <div className="space-y-6">
        {relatedArticles.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Related Articles</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {relatedArticles.map((relatedArticle) => (
                <Link key={relatedArticle.id} to={`/help/articles/${relatedArticle.slug}`}>
                  <div className="group p-3 rounded-lg border hover:border-primary hover:bg-muted/50 transition-colors">
                    <h4 className="font-medium text-sm group-hover:text-primary">
                      {relatedArticle.title}
                    </h4>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{relatedArticle.estimated_read_time} min read</span>
                    </div>
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Quick Links */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick Links</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" asChild className="w-full justify-start">
              <Link to="/help">Browse Help Centre</Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link to="/help/tickets">My Support Tickets</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
