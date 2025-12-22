import { useSearchParams, Link } from 'react-router-dom';
import { ArrowLeft, Search } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FaqAccordion } from '@/components/help/FaqAccordion';
import { useFaqSearch } from '@/hooks/useHelp';

export const FaqSearchResultsPage = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';

  const { data, isLoading, error } = useFaqSearch({ query });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-1/3" />
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
            Failed to search FAQ articles. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const results = data?.results || [];
  const total = data?.total || 0;

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button variant="ghost" asChild>
        <Link to="/help">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Help Centre
        </Link>
      </Button>

      {/* Search Results Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Search Results</h1>
        <p className="text-muted-foreground mt-2">
          Found {total} {total === 1 ? 'result' : 'results'} for "{query}"
        </p>
      </div>

      {/* Results */}
      {results.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>FAQ Articles</CardTitle>
            <CardDescription>
              Click on a question to see the full answer
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FaqAccordion articles={results} showFeedback />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <div className="flex justify-center mb-4">
                <div className="rounded-full bg-muted p-6">
                  <Search className="h-12 w-12 text-muted-foreground" />
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2">No results found</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                We couldn't find any articles matching "{query}". Try searching with different keywords
                or browse our categories.
              </p>
              <div className="flex gap-3 justify-center">
                <Button variant="outline" asChild>
                  <Link to="/help">Browse Categories</Link>
                </Button>
                <Button asChild>
                  <Link to="/help/tickets/new">Create Support Ticket</Link>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Can't Find Answer */}
      {results.length > 0 && (
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold">Didn't find what you need?</h3>
                <p className="text-muted-foreground text-sm mt-1">
                  Create a support ticket and our team will help you
                </p>
              </div>
              <Button asChild>
                <Link to="/help/tickets/new">Create Ticket</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
