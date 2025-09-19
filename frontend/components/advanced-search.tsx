/**
 * Advanced Search Component - T039 Implementation
 *
 * Provides comprehensive search functionality with:
 * - Multi-criteria filtering
 * - Faceted search
 * - Saved searches
 * - Search history
 * - Real-time suggestions
 *
 * Created: 2025-09-19
 * Task: T039 - Advanced Search Functionality
 */

'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Search, Filter, X, Clock, BookmarkPlus, Download, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Checkbox } from '@/components/ui/checkbox'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

interface SearchFilters {
  query: string
  locations: string[]
  jobTypes: string[]
  salaryRange: [number, number]
  experience: string[]
  skills: string[]
  companies: string[]
  industries: string[]
  remote: boolean
  datePosted: string
  companySize: string[]
}

interface SavedSearch {
  id: string
  name: string
  filters: SearchFilters
  created_at: string
  alert_enabled: boolean
}

interface SearchSuggestion {
  type: 'keyword' | 'location' | 'company' | 'skill'
  value: string
  count: number
}

interface SearchResult {
  id: string
  title: string
  company: string
  location: string
  salary: string
  type: string
  skills: string[]
  posted_date: string
  match_score: number
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

interface AdvancedSearchProps {
  onSearch: (filters: SearchFilters) => void
  onExport: (filters: SearchFilters, format: string) => void
  results: SearchResult[]
  isLoading: boolean
}

export default function AdvancedSearch({
  onSearch,
  onExport,
  results,
  isLoading
}: AdvancedSearchProps) {
  // State management
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    locations: [],
    jobTypes: [],
    salaryRange: [0, 20000000], // 0 to 20M yen
    experience: [],
    skills: [],
    companies: [],
    industries: [],
    remote: false,
    datePosted: 'any',
    companySize: []
  })

  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [activeTab, setActiveTab] = useState('basic')

  // Search options
  const jobTypes = ['正社員', 'アルバイト', 'パート', '契約社員', '派遣', 'インターン', 'フリーランス']
  const experienceLevels = ['未経験', '1-2年', '3-5年', '5-10年', '10年以上']
  const companySizes = ['スタートアップ', '中小企業', '大企業', '外資系']
  const industries = ['IT・Web', '金融', '製造業', '小売・サービス', '医療・福祉', '教育', '建設・不動産']
  const dateOptions = [
    { value: 'any', label: 'いつでも' },
    { value: '1day', label: '24時間以内' },
    { value: '3days', label: '3日以内' },
    { value: '1week', label: '1週間以内' },
    { value: '1month', label: '1ヶ月以内' }
  ]

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleSearch = useCallback(() => {
    // Add to search history
    if (filters.query && !searchHistory.includes(filters.query)) {
      setSearchHistory(prev => [filters.query, ...prev.slice(0, 9)])
    }

    onSearch(filters)
    setShowSuggestions(false)
  }, [filters, onSearch, searchHistory])

  const handleFilterChange = useCallback((key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }, [])

  const handleArrayFilterToggle = useCallback((key: keyof SearchFilters, value: string) => {
    setFilters(prev => {
      const currentArray = prev[key] as string[]
      const newArray = currentArray.includes(value)
        ? currentArray.filter(item => item !== value)
        : [...currentArray, value]

      return {
        ...prev,
        [key]: newArray
      }
    })
  }, [])

  const handleClearFilters = useCallback(() => {
    setFilters({
      query: '',
      locations: [],
      jobTypes: [],
      salaryRange: [0, 20000000],
      experience: [],
      skills: [],
      companies: [],
      industries: [],
      remote: false,
      datePosted: 'any',
      companySize: []
    })
  }, [])

  const handleSaveSearch = useCallback(async () => {
    const name = prompt('検索条件に名前をつけてください:')
    if (!name) return

    const savedSearch: SavedSearch = {
      id: Date.now().toString(),
      name,
      filters: { ...filters },
      created_at: new Date().toISOString(),
      alert_enabled: false
    }

    setSavedSearches(prev => [savedSearch, ...prev])

    // In real app, save to backend
    // await saveSearchToBackend(savedSearch)
  }, [filters])

  const handleLoadSavedSearch = useCallback((savedSearch: SavedSearch) => {
    setFilters(savedSearch.filters)
  }, [])

  const handleExport = useCallback((format: string) => {
    onExport(filters, format)
  }, [filters, onExport])

  // Mock suggestions
  useEffect(() => {
    if (filters.query.length > 2) {
      // In real app, fetch from API
      const mockSuggestions: SearchSuggestion[] = [
        { type: 'keyword', value: `${filters.query} エンジニア`, count: 150 },
        { type: 'keyword', value: `${filters.query} 開発者`, count: 89 },
        { type: 'company', value: `株式会社${filters.query}`, count: 12 },
        { type: 'skill', value: filters.query, count: 45 }
      ]
      setSuggestions(mockSuggestions)
      setShowSuggestions(true)
    } else {
      setShowSuggestions(false)
    }
  }, [filters.query])

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const renderFilterChips = () => {
    const activeFilters: { label: string; onRemove: () => void }[] = []

    // Add query chip
    if (filters.query) {
      activeFilters.push({
        label: `"${filters.query}"`,
        onRemove: () => handleFilterChange('query', '')
      })
    }

    // Add location chips
    filters.locations.forEach(location => {
      activeFilters.push({
        label: location,
        onRemove: () => handleArrayFilterToggle('locations', location)
      })
    })

    // Add job type chips
    filters.jobTypes.forEach(type => {
      activeFilters.push({
        label: type,
        onRemove: () => handleArrayFilterToggle('jobTypes', type)
      })
    })

    // Add other chips...
    if (filters.remote) {
      activeFilters.push({
        label: 'リモート可',
        onRemove: () => handleFilterChange('remote', false)
      })
    }

    return activeFilters.map((filter, index) => (
      <Badge key={index} variant="secondary" className="mr-2 mb-2">
        {filter.label}
        <Button
          variant="ghost"
          size="sm"
          className="ml-1 h-4 w-4 p-0"
          onClick={filter.onRemove}
        >
          <X className="h-3 w-3" />
        </Button>
      </Badge>
    ))
  }

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>高度な検索</span>
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSaveSearch}
                disabled={!filters.query && filters.locations.length === 0}
              >
                <BookmarkPlus className="h-4 w-4 mr-2" />
                保存
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    エクスポート
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => handleExport('csv')}>
                    CSV形式
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleExport('excel')}>
                    Excel形式
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleExport('pdf')}>
                    PDF形式
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CardTitle>
          <CardDescription>
            複数の条件を組み合わせて、理想の求人を見つけましょう
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Main Search Bar */}
          <div className="relative mb-4">
            <div className="flex">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="キーワード、職種、会社名で検索..."
                  value={filters.query}
                  onChange={(e) => handleFilterChange('query', e.target.value)}
                  className="pl-10 pr-10"
                  onFocus={() => setShowSuggestions(true)}
                />
                {filters.query && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1 h-8 w-8 p-0"
                    onClick={() => handleFilterChange('query', '')}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <Button onClick={handleSearch} className="ml-2" disabled={isLoading}>
                {isLoading ? '検索中...' : '検索'}
              </Button>
            </div>

            {/* Search Suggestions */}
            {showSuggestions && suggestions.length > 0 && (
              <Card className="absolute top-full left-0 right-0 z-10 mt-1">
                <CardContent className="py-2">
                  {suggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 px-2 hover:bg-muted rounded cursor-pointer"
                      onClick={() => {
                        handleFilterChange('query', suggestion.value)
                        setShowSuggestions(false)
                      }}
                    >
                      <span>{suggestion.value}</span>
                      <Badge variant="outline">{suggestion.count}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Search History */}
          {searchHistory.length > 0 && (
            <div className="mb-4">
              <div className="flex items-center mb-2">
                <Clock className="h-4 w-4 mr-2 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">最近の検索</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {searchHistory.slice(0, 5).map((query, index) => (
                  <Badge
                    key={index}
                    variant="outline"
                    className="cursor-pointer"
                    onClick={() => handleFilterChange('query', query)}
                  >
                    {query}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Active Filters */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">適用中のフィルター</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearFilters}
                className="text-muted-foreground"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                クリア
              </Button>
            </div>
            <div className="flex flex-wrap">
              {renderFilterChips()}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">基本条件</TabsTrigger>
          <TabsTrigger value="advanced">詳細条件</TabsTrigger>
          <TabsTrigger value="saved">保存済み検索</TabsTrigger>
          <TabsTrigger value="results">検索結果 ({results.length})</TabsTrigger>
        </TabsList>

        {/* Basic Filters */}
        <TabsContent value="basic" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Job Types */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">雇用形態</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {jobTypes.map(type => (
                  <div key={type} className="flex items-center space-x-2">
                    <Checkbox
                      id={`jobtype-${type}`}
                      checked={filters.jobTypes.includes(type)}
                      onCheckedChange={() => handleArrayFilterToggle('jobTypes', type)}
                    />
                    <label htmlFor={`jobtype-${type}`} className="text-sm">
                      {type}
                    </label>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Experience */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">経験年数</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {experienceLevels.map(level => (
                  <div key={level} className="flex items-center space-x-2">
                    <Checkbox
                      id={`exp-${level}`}
                      checked={filters.experience.includes(level)}
                      onCheckedChange={() => handleArrayFilterToggle('experience', level)}
                    />
                    <label htmlFor={`exp-${level}`} className="text-sm">
                      {level}
                    </label>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Date Posted */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">掲載期間</CardTitle>
              </CardHeader>
              <CardContent>
                <Select
                  value={filters.datePosted}
                  onValueChange={(value) => handleFilterChange('datePosted', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {dateOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>
          </div>

          {/* Salary Range */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">年収範囲</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Slider
                  value={filters.salaryRange}
                  onValueChange={(value) => handleFilterChange('salaryRange', value as [number, number])}
                  max={20000000}
                  min={0}
                  step={500000}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>{filters.salaryRange[0].toLocaleString()}円</span>
                  <span>{filters.salaryRange[1].toLocaleString()}円</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Remote Work */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remote"
                  checked={filters.remote}
                  onCheckedChange={(checked) => handleFilterChange('remote', checked)}
                />
                <label htmlFor="remote" className="text-sm font-medium">
                  リモートワーク可
                </label>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Filters */}
        <TabsContent value="advanced" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Industries */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">業界</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {industries.map(industry => (
                  <div key={industry} className="flex items-center space-x-2">
                    <Checkbox
                      id={`industry-${industry}`}
                      checked={filters.industries.includes(industry)}
                      onCheckedChange={() => handleArrayFilterToggle('industries', industry)}
                    />
                    <label htmlFor={`industry-${industry}`} className="text-sm">
                      {industry}
                    </label>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Company Size */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">企業規模</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {companySizes.map(size => (
                  <div key={size} className="flex items-center space-x-2">
                    <Checkbox
                      id={`size-${size}`}
                      checked={filters.companySize.includes(size)}
                      onCheckedChange={() => handleArrayFilterToggle('companySize', size)}
                    />
                    <label htmlFor={`size-${size}`} className="text-sm">
                      {size}
                    </label>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Saved Searches */}
        <TabsContent value="saved" className="space-y-4">
          {savedSearches.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">保存された検索はありません</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {savedSearches.map(savedSearch => (
                <Card key={savedSearch.id} className="cursor-pointer hover:bg-muted/50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div onClick={() => handleLoadSavedSearch(savedSearch)}>
                        <h4 className="font-medium">{savedSearch.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {new Date(savedSearch.created_at).toLocaleDateString('ja-JP')}
                        </p>
                      </div>
                      <Button variant="ghost" size="sm">
                        読み込み
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Search Results */}
        <TabsContent value="results">
          <Card>
            <CardHeader>
              <CardTitle>検索結果</CardTitle>
              <CardDescription>
                {results.length} 件の求人が見つかりました
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-2 text-muted-foreground">検索中...</p>
                </div>
              ) : results.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">
                    検索条件に一致する求人が見つかりませんでした
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {results.map(result => (
                    <Card key={result.id}>
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-semibold text-lg">{result.title}</h3>
                            <p className="text-muted-foreground">{result.company}</p>
                            <div className="flex items-center space-x-4 mt-2 text-sm">
                              <span>{result.location}</span>
                              <span>{result.salary}</span>
                              <span>{result.type}</span>
                            </div>
                            <div className="flex flex-wrap gap-1 mt-2">
                              {result.skills.map(skill => (
                                <Badge key={skill} variant="outline">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div className="text-right">
                            <Badge variant="secondary">
                              マッチ度 {result.match_score}%
                            </Badge>
                            <p className="text-xs text-muted-foreground mt-1">
                              {result.posted_date}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}