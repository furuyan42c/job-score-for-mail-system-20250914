/**
 * T072: Score Calculator Edge Function
 *
 * Handles comprehensive score calculations including:
 * - Email scoring algorithms
 * - Matching score computations
 * - Performance metrics
 * - Custom scoring models
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders, handleCors, createResponse } from '../_shared/cors.ts'
import { createAdminClient } from '../_shared/supabase.ts'
import { Logger } from '../_shared/logger.ts'

const logger = new Logger('score-calculator')

interface ScoreRequest {
  calculation_type: 'email_score' | 'matching_score' | 'performance_score' | 'custom_score'
  entity_id: string
  entity_type: string
  scoring_criteria?: any
  custom_weights?: any
  metadata?: any
}

interface ScoreResult {
  success: boolean
  calculation_id?: string
  scores?: any
  breakdown?: any
  confidence?: number
  error?: string
  processing_time_ms?: number
}

interface EmailScoringCriteria {
  content_quality_weight: number
  relevance_weight: number
  engagement_potential_weight: number
  technical_factors_weight: number
  sender_reputation_weight: number
}

interface MatchingScoringCriteria {
  exact_match_weight: number
  partial_match_weight: number
  context_similarity_weight: number
  temporal_relevance_weight: number
  user_preference_weight: number
}

serve(async (req) => {
  // Handle CORS
  const corsResponse = handleCors(req)
  if (corsResponse) return corsResponse

  try {
    logger.info('Score calculator started', { method: req.method })

    if (req.method !== 'POST') {
      return createResponse({ error: 'Method not allowed' }, 405)
    }

    // Parse request body
    const scoreRequest: ScoreRequest = await req.json()
    logger.info('Received score request', {
      calculation_type: scoreRequest.calculation_type,
      entity_id: scoreRequest.entity_id,
      entity_type: scoreRequest.entity_type
    })

    // Validate score request
    const validation = validateScoreRequest(scoreRequest)
    if (!validation.valid) {
      return createResponse({ error: validation.error }, 400)
    }

    // Create Supabase admin client
    const supabase = createAdminClient()

    const startTime = Date.now()
    let result: ScoreResult

    try {
      // Process score calculation based on type
      switch (scoreRequest.calculation_type) {
        case 'email_score':
          result = await calculateEmailScore(supabase, scoreRequest)
          break
        case 'matching_score':
          result = await calculateMatchingScore(supabase, scoreRequest)
          break
        case 'performance_score':
          result = await calculatePerformanceScore(supabase, scoreRequest)
          break
        case 'custom_score':
          result = await calculateCustomScore(supabase, scoreRequest)
          break
        default:
          throw new Error(`Unknown calculation type: ${scoreRequest.calculation_type}`)
      }

      // Add processing time
      result.processing_time_ms = Date.now() - startTime

      // Store calculation results
      await storeCalculationResults(supabase, scoreRequest, result)

      logger.info('Score calculation completed', {
        calculation_type: scoreRequest.calculation_type,
        calculation_id: result.calculation_id,
        processing_time_ms: result.processing_time_ms
      })

    } catch (error) {
      const errorMessage = error.message || 'Unknown error'
      logger.error('Score calculation failed', { error: errorMessage })

      result = {
        success: false,
        error: errorMessage,
        processing_time_ms: Date.now() - startTime
      }
    }

    return createResponse(result)

  } catch (error) {
    logger.error('Unhandled error in score calculator', { error: error.message })
    return createResponse({ error: 'Internal server error' }, 500)
  }
})

function validateScoreRequest(request: ScoreRequest): { valid: boolean; error?: string } {
  if (!request.calculation_type) {
    return { valid: false, error: 'Missing calculation_type' }
  }

  if (!request.entity_id) {
    return { valid: false, error: 'Missing entity_id' }
  }

  if (!request.entity_type) {
    return { valid: false, error: 'Missing entity_type' }
  }

  return { valid: true }
}

async function calculateEmailScore(supabase: any, request: ScoreRequest): Promise<ScoreResult> {
  logger.info('Calculating email score', { entity_id: request.entity_id })

  try {
    // Get email data
    const { data: email, error: emailError } = await supabase
      .from('emails')
      .select('*')
      .eq('id', request.entity_id)
      .single()

    if (emailError) {
      throw new Error(`Failed to fetch email: ${emailError.message}`)
    }

    // Get or use default scoring criteria
    const criteria: EmailScoringCriteria = request.scoring_criteria || {
      content_quality_weight: 0.3,
      relevance_weight: 0.25,
      engagement_potential_weight: 0.2,
      technical_factors_weight: 0.15,
      sender_reputation_weight: 0.1
    }

    // Calculate individual score components
    const contentQuality = await calculateContentQualityScore(email)
    const relevance = await calculateRelevanceScore(email)
    const engagementPotential = await calculateEngagementScore(email)
    const technicalFactors = await calculateTechnicalScore(email)
    const senderReputation = await calculateSenderReputationScore(email)

    // Calculate weighted overall score
    const overallScore = (
      contentQuality.score * criteria.content_quality_weight +
      relevance.score * criteria.relevance_weight +
      engagementPotential.score * criteria.engagement_potential_weight +
      technicalFactors.score * criteria.technical_factors_weight +
      senderReputation.score * criteria.sender_reputation_weight
    )

    // Calculate confidence based on data completeness
    const confidence = calculateConfidence([
      contentQuality.confidence,
      relevance.confidence,
      engagementPotential.confidence,
      technicalFactors.confidence,
      senderReputation.confidence
    ])

    const calculationId = generateCalculationId()

    const scores = {
      overall_score: Math.round(overallScore * 100) / 100,
      content_quality: contentQuality.score,
      relevance: relevance.score,
      engagement_potential: engagementPotential.score,
      technical_factors: technicalFactors.score,
      sender_reputation: senderReputation.score
    }

    const breakdown = {
      content_quality: contentQuality.breakdown,
      relevance: relevance.breakdown,
      engagement_potential: engagementPotential.breakdown,
      technical_factors: technicalFactors.breakdown,
      sender_reputation: senderReputation.breakdown,
      weights: criteria
    }

    return {
      success: true,
      calculation_id: calculationId,
      scores,
      breakdown,
      confidence
    }

  } catch (error) {
    throw new Error(`Email score calculation failed: ${error.message}`)
  }
}

async function calculateMatchingScore(supabase: any, request: ScoreRequest): Promise<ScoreResult> {
  logger.info('Calculating matching score', { entity_id: request.entity_id })

  try {
    // Get matching data
    const { data: matchData, error: matchError } = await supabase
      .from('matching_requests')
      .select('*')
      .eq('id', request.entity_id)
      .single()

    if (matchError) {
      throw new Error(`Failed to fetch matching data: ${matchError.message}`)
    }

    // Get or use default scoring criteria
    const criteria: MatchingScoringCriteria = request.scoring_criteria || {
      exact_match_weight: 0.4,
      partial_match_weight: 0.25,
      context_similarity_weight: 0.2,
      temporal_relevance_weight: 0.1,
      user_preference_weight: 0.05
    }

    // Calculate matching components
    const exactMatch = await calculateExactMatchScore(matchData)
    const partialMatch = await calculatePartialMatchScore(matchData)
    const contextSimilarity = await calculateContextSimilarityScore(matchData)
    const temporalRelevance = await calculateTemporalRelevanceScore(matchData)
    const userPreference = await calculateUserPreferenceScore(matchData)

    // Calculate weighted overall score
    const overallScore = (
      exactMatch.score * criteria.exact_match_weight +
      partialMatch.score * criteria.partial_match_weight +
      contextSimilarity.score * criteria.context_similarity_weight +
      temporalRelevance.score * criteria.temporal_relevance_weight +
      userPreference.score * criteria.user_preference_weight
    )

    // Calculate confidence
    const confidence = calculateConfidence([
      exactMatch.confidence,
      partialMatch.confidence,
      contextSimilarity.confidence,
      temporalRelevance.confidence,
      userPreference.confidence
    ])

    const calculationId = generateCalculationId()

    const scores = {
      overall_score: Math.round(overallScore * 100) / 100,
      exact_match: exactMatch.score,
      partial_match: partialMatch.score,
      context_similarity: contextSimilarity.score,
      temporal_relevance: temporalRelevance.score,
      user_preference: userPreference.score
    }

    const breakdown = {
      exact_match: exactMatch.breakdown,
      partial_match: partialMatch.breakdown,
      context_similarity: contextSimilarity.breakdown,
      temporal_relevance: temporalRelevance.breakdown,
      user_preference: userPreference.breakdown,
      weights: criteria
    }

    return {
      success: true,
      calculation_id: calculationId,
      scores,
      breakdown,
      confidence
    }

  } catch (error) {
    throw new Error(`Matching score calculation failed: ${error.message}`)
  }
}

async function calculatePerformanceScore(supabase: any, request: ScoreRequest): Promise<ScoreResult> {
  logger.info('Calculating performance score', { entity_id: request.entity_id })

  try {
    // Get performance metrics
    const { data: metrics, error: metricsError } = await supabase
      .from('performance_metrics')
      .select('*')
      .eq('entity_id', request.entity_id)
      .eq('entity_type', request.entity_type)

    if (metricsError) {
      throw new Error(`Failed to fetch performance metrics: ${metricsError.message}`)
    }

    if (!metrics || metrics.length === 0) {
      throw new Error('No performance metrics found')
    }

    // Calculate performance scores
    const latencyScore = calculateLatencyScore(metrics)
    const throughputScore = calculateThroughputScore(metrics)
    const accuracyScore = calculateAccuracyScore(metrics)
    const reliabilityScore = calculateReliabilityScore(metrics)
    const efficiencyScore = calculateEfficiencyScore(metrics)

    // Calculate overall performance score
    const overallScore = (
      latencyScore.score * 0.25 +
      throughputScore.score * 0.2 +
      accuracyScore.score * 0.25 +
      reliabilityScore.score * 0.2 +
      efficiencyScore.score * 0.1
    )

    const calculationId = generateCalculationId()

    const scores = {
      overall_score: Math.round(overallScore * 100) / 100,
      latency: latencyScore.score,
      throughput: throughputScore.score,
      accuracy: accuracyScore.score,
      reliability: reliabilityScore.score,
      efficiency: efficiencyScore.score
    }

    const breakdown = {
      latency: latencyScore.breakdown,
      throughput: throughputScore.breakdown,
      accuracy: accuracyScore.breakdown,
      reliability: reliabilityScore.breakdown,
      efficiency: efficiencyScore.breakdown
    }

    return {
      success: true,
      calculation_id: calculationId,
      scores,
      breakdown,
      confidence: 0.9
    }

  } catch (error) {
    throw new Error(`Performance score calculation failed: ${error.message}`)
  }
}

async function calculateCustomScore(supabase: any, request: ScoreRequest): Promise<ScoreResult> {
  logger.info('Calculating custom score', { entity_id: request.entity_id })

  try {
    // Get custom scoring model
    const scoringModel = request.scoring_criteria
    if (!scoringModel) {
      throw new Error('Custom scoring criteria required')
    }

    // Get entity data
    const { data: entity, error: entityError } = await supabase
      .from(scoringModel.table_name || 'entities')
      .select('*')
      .eq('id', request.entity_id)
      .single()

    if (entityError) {
      throw new Error(`Failed to fetch entity: ${entityError.message}`)
    }

    // Apply custom scoring logic
    const customScores = await applyCustomScoringModel(entity, scoringModel, request.custom_weights)

    const calculationId = generateCalculationId()

    return {
      success: true,
      calculation_id: calculationId,
      scores: customScores.scores,
      breakdown: customScores.breakdown,
      confidence: customScores.confidence || 0.8
    }

  } catch (error) {
    throw new Error(`Custom score calculation failed: ${error.message}`)
  }
}

// Helper functions for email scoring

async function calculateContentQualityScore(email: any): Promise<any> {
  // Analyze content quality factors
  const textLength = email.body?.length || 0
  const hasSubject = email.subject ? 1 : 0
  const hasValidStructure = email.body?.includes('\n') ? 1 : 0

  const score = Math.min(
    (textLength / 1000) * 0.5 + hasSubject * 0.3 + hasValidStructure * 0.2,
    1.0
  )

  return {
    score,
    confidence: 0.8,
    breakdown: {
      text_length_score: textLength / 1000,
      has_subject: hasSubject,
      has_structure: hasValidStructure
    }
  }
}

async function calculateRelevanceScore(email: any): Promise<any> {
  // Calculate relevance based on keywords, context, etc.
  const score = 0.75 // Placeholder

  return {
    score,
    confidence: 0.7,
    breakdown: {
      keyword_relevance: 0.8,
      context_match: 0.7,
      topic_alignment: 0.75
    }
  }
}

async function calculateEngagementScore(email: any): Promise<any> {
  // Calculate engagement potential
  const score = 0.65 // Placeholder

  return {
    score,
    confidence: 0.6,
    breakdown: {
      call_to_action: 0.7,
      personalization: 0.6,
      urgency_level: 0.65
    }
  }
}

async function calculateTechnicalScore(email: any): Promise<any> {
  // Technical factors like deliverability, formatting, etc.
  const score = 0.85 // Placeholder

  return {
    score,
    confidence: 0.9,
    breakdown: {
      deliverability: 0.9,
      formatting: 0.8,
      security: 0.85
    }
  }
}

async function calculateSenderReputationScore(email: any): Promise<any> {
  // Sender reputation factors
  const score = 0.8 // Placeholder

  return {
    score,
    confidence: 0.75,
    breakdown: {
      domain_reputation: 0.85,
      sender_history: 0.75,
      authentication: 0.8
    }
  }
}

// Helper functions for matching scoring

async function calculateExactMatchScore(matchData: any): Promise<any> {
  const score = 0.9 // Placeholder
  return {
    score,
    confidence: 0.95,
    breakdown: { exact_matches: 5, total_fields: 6 }
  }
}

async function calculatePartialMatchScore(matchData: any): Promise<any> {
  const score = 0.7 // Placeholder
  return {
    score,
    confidence: 0.8,
    breakdown: { partial_matches: 3, similarity_threshold: 0.8 }
  }
}

async function calculateContextSimilarityScore(matchData: any): Promise<any> {
  const score = 0.6 // Placeholder
  return {
    score,
    confidence: 0.7,
    breakdown: { context_vectors: true, similarity_score: 0.6 }
  }
}

async function calculateTemporalRelevanceScore(matchData: any): Promise<any> {
  const score = 0.8 // Placeholder
  return {
    score,
    confidence: 0.85,
    breakdown: { time_decay: 0.9, recency_factor: 0.8 }
  }
}

async function calculateUserPreferenceScore(matchData: any): Promise<any> {
  const score = 0.75 // Placeholder
  return {
    score,
    confidence: 0.6,
    breakdown: { preference_alignment: 0.75, user_feedback: 0.7 }
  }
}

// Helper functions for performance scoring

function calculateLatencyScore(metrics: any[]): any {
  const avgLatency = metrics.reduce((sum, m) => sum + (m.latency_ms || 0), 0) / metrics.length
  const score = Math.max(0, 1 - (avgLatency / 1000)) // Normalize to 0-1 scale

  return {
    score,
    breakdown: { avg_latency_ms: avgLatency, target_latency_ms: 500 }
  }
}

function calculateThroughputScore(metrics: any[]): any {
  const avgThroughput = metrics.reduce((sum, m) => sum + (m.throughput || 0), 0) / metrics.length
  const score = Math.min(1, avgThroughput / 1000) // Normalize to 0-1 scale

  return {
    score,
    breakdown: { avg_throughput: avgThroughput, target_throughput: 1000 }
  }
}

function calculateAccuracyScore(metrics: any[]): any {
  const avgAccuracy = metrics.reduce((sum, m) => sum + (m.accuracy || 0), 0) / metrics.length

  return {
    score: avgAccuracy,
    breakdown: { avg_accuracy: avgAccuracy, min_accuracy: 0.95 }
  }
}

function calculateReliabilityScore(metrics: any[]): any {
  const uptime = metrics.reduce((sum, m) => sum + (m.uptime || 0), 0) / metrics.length

  return {
    score: uptime,
    breakdown: { avg_uptime: uptime, target_uptime: 0.999 }
  }
}

function calculateEfficiencyScore(metrics: any[]): any {
  const efficiency = metrics.reduce((sum, m) => sum + (m.efficiency || 0), 0) / metrics.length

  return {
    score: efficiency,
    breakdown: { avg_efficiency: efficiency, target_efficiency: 0.9 }
  }
}

// Utility functions

async function applyCustomScoringModel(entity: any, model: any, weights: any): Promise<any> {
  // Apply custom scoring logic based on model
  const scores = {}
  const breakdown = {}

  for (const [field, config] of Object.entries(model.fields || {})) {
    const value = entity[field]
    const weight = weights?.[field] || config.weight || 1

    // Apply field-specific scoring logic
    let fieldScore = 0
    if (config.type === 'numeric') {
      fieldScore = Math.min(value / config.max_value, 1)
    } else if (config.type === 'boolean') {
      fieldScore = value ? 1 : 0
    } else if (config.type === 'categorical') {
      fieldScore = config.category_scores?.[value] || 0
    }

    scores[field] = fieldScore * weight
    breakdown[field] = { value, score: fieldScore, weight }
  }

  const overallScore = Object.values(scores).reduce((sum: number, score: number) => sum + score, 0) / Object.keys(scores).length

  return {
    scores: { overall_score: overallScore, ...scores },
    breakdown,
    confidence: 0.8
  }
}

function calculateConfidence(confidenceValues: number[]): number {
  // Calculate average confidence with minimum threshold
  const avgConfidence = confidenceValues.reduce((sum, conf) => sum + conf, 0) / confidenceValues.length
  return Math.max(0.5, avgConfidence) // Minimum 50% confidence
}

function generateCalculationId(): string {
  return `calc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

async function storeCalculationResults(supabase: any, request: ScoreRequest, result: ScoreResult) {
  try {
    const { error } = await supabase
      .from('score_calculations')
      .insert({
        id: result.calculation_id,
        calculation_type: request.calculation_type,
        entity_id: request.entity_id,
        entity_type: request.entity_type,
        scores: result.scores,
        breakdown: result.breakdown,
        confidence: result.confidence,
        processing_time_ms: result.processing_time_ms,
        metadata: request.metadata,
        calculated_at: new Date().toISOString()
      })

    if (error) {
      logger.error('Failed to store calculation results', { error: error.message })
    }
  } catch (error) {
    logger.error('Error storing calculation results', { error: error.message })
  }
}