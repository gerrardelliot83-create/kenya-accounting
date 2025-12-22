import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FaqAccordion } from '@/components/help/FaqAccordion';
import { useFaqCategories, useFaqArticles } from '@/hooks/useHelp';

export const FaqCategoryPage = () => {
  const { categoryId } = useParams<{ categoryId: string }>();

  const { data: categories } = useFaqCategories();
  const { data: articles, isLoading, error } = useFaqArticles(categoryId);

  const category = categories?.find((c) => c.id === categoryId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-4 w-1/2" />
        <Card>
          <CardContent className="pt-6 space-y-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
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
            Failed to load FAQ articles. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button variant="ghost" asChild>
        <Link to="/help">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Help Centre
        </Link>
      </Button>

      {/* Category Header */}
      {category && (
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{category.name}</h1>
          <p className="text-muted-foreground mt-2">{category.description}</p>
          <p className="text-sm text-muted-foreground mt-1">
            {category.article_count} {category.article_count === 1 ? 'article' : 'articles'}
          </p>
        </div>
      )}

      {/* FAQ Articles */}
      {articles && articles.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Frequently Asked Questions</CardTitle>
            <CardDescription>
              Click on a question to see the answer
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FaqAccordion articles={articles} showFeedback />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                No FAQ articles found in this category yet.
              </p>
              <Button variant="outline" asChild className="mt-4">
                <Link to="/help">Browse Other Categories</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Still Need Help */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h3 className="font-semibold">Still need help?</h3>
              <p className="text-muted-foreground text-sm mt-1">
                Contact our support team and we'll get back to you
              </p>
            </div>
            <Button asChild>
              <Link to="/help/tickets/new">Create Support Ticket</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
