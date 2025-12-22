import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, HelpCircle, FileText, BookOpen, Ticket } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useFaqCategories, useHelpArticles } from '@/hooks/useHelp';

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  default: HelpCircle,
  billing: FileText,
  technical: BookOpen,
  features: Ticket,
};

export const HelpCentrePage = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const { data: categories, isLoading: categoriesLoading } = useFaqCategories();
  const { data: articles, isLoading: articlesLoading } = useHelpArticles();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/help/faq/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const popularArticles = articles?.slice(0, 4) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Help Centre</h1>
        <p className="text-muted-foreground">
          Find answers, browse guides, or contact support
        </p>
      </div>

      {/* Search Bar - Prominent */}
      <Card className="border-2">
        <CardContent className="pt-6">
          <form onSubmit={handleSearch}>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search for help articles, FAQs, or guides..."
                  className="pl-9 h-12 text-base"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Button type="submit" size="lg" className="px-8">
                Search
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* FAQ Categories Grid */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Browse by Category</h2>
        {categoriesLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-full" />
                </CardHeader>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {categories?.map((category) => {
              const IconComponent = categoryIcons[category.icon || 'default'] || categoryIcons.default;

              return (
                <Link key={category.id} to={`/help/faq/${category.id}`}>
                  <Card className="h-full transition-all hover:shadow-md hover:border-primary">
                    <CardHeader>
                      <div className="flex items-start gap-3">
                        <div className="rounded-lg bg-primary/10 p-2">
                          <IconComponent className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1">
                          <CardTitle className="text-lg">{category.name}</CardTitle>
                          <CardDescription className="mt-1.5">
                            {category.description}
                          </CardDescription>
                          <p className="text-xs text-muted-foreground mt-2">
                            {category.article_count} articles
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Popular Articles Section */}
      {!articlesLoading && popularArticles.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Popular Articles</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {popularArticles.map((article) => (
              <Link key={article.id} to={`/help/articles/${article.slug}`}>
                <Card className="transition-all hover:shadow-md hover:border-primary">
                  <CardHeader>
                    <CardTitle className="text-base">{article.title}</CardTitle>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{article.category}</span>
                      <span>·</span>
                      <span>{article.estimated_read_time} min read</span>
                      <span>·</span>
                      <span>{article.view_count} views</span>
                    </div>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Can't Find Answer CTA */}
      <Card className="bg-muted/50 border-2 border-dashed">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h3 className="font-semibold text-lg">Can't find what you're looking for?</h3>
              <p className="text-muted-foreground mt-1">
                Create a support ticket and our team will help you out
              </p>
            </div>
            <Button asChild size="lg">
              <Link to="/help/tickets/new">Create Ticket</Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              My Support Tickets
            </CardTitle>
            <CardDescription>
              View and manage your existing support tickets
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" asChild className="w-full">
              <Link to="/help/tickets">View My Tickets</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              All Help Articles
            </CardTitle>
            <CardDescription>
              Browse our complete collection of guides
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" asChild className="w-full">
              <Link to="/help/articles">Browse Articles</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
