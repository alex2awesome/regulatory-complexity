"""Optional reference-anchored source-bias hierarchy for V6.

The declaration is deliberately separate from source-comparison review.  It is
a model parameterization, not evidence that a source type is reliable or that
two reports measure the same estimand.  Every sampled coordinate has an
independent standard-normal prior; positive spreads and effective offsets are
deterministic transforms.
"""
from __future__ import annotations

import math
import re

import numpy as np
from scipy.linalg import helmert
from scipy.special import ndtri

from .latent_gaussian import summary
from .cohort_histograms import cohort_histogram_observations
from .source_comparisons import comparison_digest


VERSION = 'source-offset-hierarchy/1'
HISTOGRAM_REFERENCE_VERSION = 'source-offset-hierarchy/2'
UNRESOLVED = {'unknown', 'unspecified', 'unresolved', 'tbd', 'not_reviewed'}
DECLARATION_KEYS = {'schema_version', 'source_family_grouping', 'elapsed_time_unit',
                    'reference_type', 'type_scale_prior', 'document_scale_prior',
                    'documents'}
PRIOR_KEYS = {'median', 'log_sd'}
DOCUMENT_KEYS = {'document_id', 'source_type'}
HISTOGRAM_REFERENCE_KEYS = {'program_id', 'cohort_id', 'source_family', 'cohort_sha256'}


def _exact_keys(value, expected, where):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f'{where}: unexpected or missing fields')


def _name(value, where):
    if (not isinstance(value, str) or not value.strip() or value != value.strip()
            or value.lower() in UNRESOLVED):
        raise ValueError(f'{where}: require an explicit resolved nonempty string')


def _prior(value, where):
    _exact_keys(value, PRIOR_KEYS, where)
    for key in PRIOR_KEYS:
        item = value[key]
        if (isinstance(item, bool) or not isinstance(item, (int, float))
                or not math.isfinite(item) or item <= 0):
            raise ValueError(f'{where}: median and log_sd must be positive finite numbers')
    return dict(median=float(value['median']), log_sd=float(value['log_sd']))


def _histogram_references(references, programs, elapsed_time_unit):
    """Resolve declared exact-cohort anchors, not their substantive credibility.

    Hashes bind original input objects. The histogram contract is validated
    again here so this helper cannot silently accept a nonexact stand-in.
    These references add no likelihood factor and no reporting offset.
    """
    if not isinstance(references, list) or not references:
        raise ValueError('Histogram reference v2 requires a nonempty anchor list')
    if not isinstance(programs, list):
        raise ValueError('Histogram references require original input programs')
    program_map = {}
    for program in programs:
        ident = program['id']
        if ident in program_map:
            raise ValueError('Ambiguous histogram reference program identity')
        program_map[ident] = program
    result, seen = [], set()
    for item in references:
        _exact_keys(item, HISTOGRAM_REFERENCE_KEYS, 'histogram reference')
        for field in HISTOGRAM_REFERENCE_KEYS - {'cohort_sha256'}:
            _name(item[field], 'histogram reference ' + field)
        digest = item['cohort_sha256']
        if not isinstance(digest, str) or re.fullmatch('[0-9a-f]{64}', digest) is None:
            raise ValueError('Histogram reference requires a canonical SHA-256')
        identity = (item['program_id'], item['cohort_id'])
        if identity in seen:
            raise ValueError('Repeated histogram reference')
        seen.add(identity)
        program = program_map.get(item['program_id'])
        matches = [] if program is None else [
            c for c in program.get('histogram_cohorts', [])
            if c.get('cohort_id') == item['cohort_id']]
        if len(matches) != 1:
            raise ValueError('Histogram reference is missing or ambiguous')
        cohort = matches[0]
        if comparison_digest(cohort) != digest:
            raise ValueError('Histogram reference cohort binding is stale')
        cohort_histogram_observations(cohort)
        if cohort['source_family'] != item['source_family']:
            raise ValueError('Histogram reference source family differs from cohort')
        if cohort['time_unit'] != elapsed_time_unit:
            raise ValueError('Histogram reference calendar differs from model')
        if len(cohort['bin_counts']) < 2:
            raise ValueError('Histogram reference needs a nontrivial duration partition')
        result.append(dict(item, factor_id=cohort['id'],
                           sample_size=cohort['sample_size'],
                           bin_count=len(cohort['bin_counts'])))
    return tuple(result)


class SourceOffsetHierarchy:
    """Strict declaration, coordinate layout and deterministic transforms."""

    def __init__(self, declaration, source_families, elapsed_time_unit, layout,
                 comparison_review=None, *, programs=None):
        version = declaration.get('schema_version') if isinstance(declaration, dict) else None
        if version not in {VERSION, HISTOGRAM_REFERENCE_VERSION}:
            raise ValueError('Unsupported source offset hierarchy version')
        keys = DECLARATION_KEYS | ({'reference_histogram_cohorts'}
                                  if version == HISTOGRAM_REFERENCE_VERSION else set())
        _exact_keys(declaration, keys, 'source offset hierarchy')
        if declaration['source_family_grouping'] != 'document':
            raise ValueError('Source offset hierarchy requires document-grouped source families')
        if declaration['elapsed_time_unit'] != elapsed_time_unit:
            raise ValueError('Source offset hierarchy calendar differs from the model; no conversion is implicit')
        _name(declaration['reference_type'], 'reference_type')
        self.reference_type = declaration['reference_type']
        self.type_scale_prior = _prior(declaration['type_scale_prior'], 'type_scale_prior')
        self.document_scale_prior = _prior(declaration['document_scale_prior'], 'document_scale_prior')
        self.reference_histogram_cohorts = (
            _histogram_references(declaration['reference_histogram_cohorts'],
                                  programs, elapsed_time_unit)
            if version == HISTOGRAM_REFERENCE_VERSION else ())

        documents = declaration['documents']
        if not isinstance(documents, list) or not documents:
            raise ValueError('Source offset hierarchy requires document mappings')
        mapping = {}
        for item in documents:
            _exact_keys(item, DOCUMENT_KEYS, 'source document mapping')
            _name(item['document_id'], 'document_id')
            _name(item['source_type'], 'source_type')
            if item['document_id'] in mapping:
                raise ValueError('Source offset hierarchy document IDs must be distinct')
            mapping[item['document_id']] = item['source_type']
        expected = set(source_families)
        if set(mapping) != expected:
            missing = sorted(expected - set(mapping))
            extra = sorted(set(mapping) - expected)
            raise ValueError(f'Source document mapping must exactly cover duration source families; missing={missing}, extra={extra}')
        if comparison_review is not None:
            # source_comparison_report has already validated the full review and
            # its hashes.  This additional gate only prevents two supplied
            # declarations from assigning the same document incompatible types.
            for block in comparison_review['blocks']:
                for member in block['members']:
                    document = member['document_id']
                    if document in mapping and mapping[document] != member['source_type']:
                        raise ValueError('Source hierarchy and comparison review assign conflicting types to one document')
        for anchor in self.reference_histogram_cohorts:
            if (anchor['source_family'] in mapping and
                    mapping[anchor['source_family']] != self.reference_type):
                raise ValueError('Histogram reference family has a conflicting report source type')
        types = sorted(set(mapping.values()))
        if self.reference_type not in types and not self.reference_histogram_cohorts:
            raise ValueError('Reference source type has no mapped duration document')
        nonreference = [name for name in types if name != self.reference_type]
        if not nonreference:
            raise ValueError('Source offset hierarchy requires a nonreference source type')

        self.documents = tuple(source_families)
        self.document_type = dict(mapping)
        self.types = tuple([self.reference_type] + nonreference)
        self.documents_by_type = {
            source_type: tuple(name for name in self.documents if mapping[name] == source_type)
            for source_type in self.types
        }
        self.type_scale_coordinate = int(layout.add('source_hierarchy:type_scale', 1)[0])
        raw = layout.add('source_hierarchy:type_effects', len(nonreference))
        self.type_effect_coordinates = np.asarray(raw, dtype=int)
        self.type_coordinates = dict(zip(nonreference, map(int, raw)))
        replicated = [name for name in self.types if len(self.documents_by_type[name]) >= 2]
        self.document_scale_coordinate = None
        self.document_coordinates = {}
        self.document_bases = {}
        if replicated:
            self.document_scale_coordinate = int(layout.add('source_hierarchy:document_scale', 1)[0])
            for source_type in replicated:
                n = len(self.documents_by_type[source_type])
                coordinates = layout.add('source_hierarchy:document_effects:' + source_type, n - 1)
                self.document_coordinates[source_type] = coordinates
                # scipy's rows are an orthonormal contrast basis.  Transposing
                # maps n-1 iid normals to n residuals whose sum is exactly zero.
                self.document_bases[source_type] = helmert(n).T
        pieces = [np.array([self.type_scale_coordinate], dtype=int), raw]
        if self.document_scale_coordinate is not None:
            pieces.append(np.array([self.document_scale_coordinate], dtype=int))
            pieces.extend(self.document_coordinates[name] for name in replicated)
        self.coordinates = np.concatenate(pieces)
        self._coordinate_positions = {int(coordinate): index
                                      for index,coordinate in enumerate(self.coordinates)}

    def sampler_blocks(self, *, split=False):
        """Return exact-prior ESS blocks without changing the coordinate target."""
        if not split:
            return (self.coordinates,)
        blocks = [np.array([self.type_scale_coordinate], dtype=int)]
        if len(self.type_effect_coordinates):
            blocks.append(self.type_effect_coordinates)
        if self.document_scale_coordinate is not None:
            blocks.append(np.array([self.document_scale_coordinate], dtype=int))
            blocks.extend(np.asarray(self.document_coordinates[name], dtype=int)
                          for name in self.types if name in self.document_coordinates)
        return tuple(blocks)

    @property
    def interweave_levels(self):
        levels = ['type']
        if self.document_scale_coordinate is not None:
            levels.append('document')
        return tuple(levels)

    def interweave_proposal(self, z, level, epsilon):
        """Hold actual effects fixed while moving one lognormal scale coordinate.

        Returns a fresh state and the Gaussian-prior plus proposal-Jacobian log
        correction.  The likelihood is intentionally evaluated by the enclosing
        model, both as a correctness check and to cover floating-point drift.
        Nonrepresentable proposals return ``None`` without mutating ``z``.
        """
        z = np.asarray(z, dtype=float)
        if z.ndim != 1 or not np.isfinite(z).all() or not math.isfinite(epsilon):
            return None
        if level == 'type':
            scale_coordinate = self.type_scale_coordinate
            effect_coordinates = self.type_effect_coordinates
            log_sd = self.type_scale_prior['log_sd']
        elif level == 'document' and self.document_scale_coordinate is not None:
            scale_coordinate = self.document_scale_coordinate
            effect_coordinates = np.concatenate([
                np.asarray(self.document_coordinates[name], dtype=int)
                for name in self.types if name in self.document_coordinates])
            log_sd = self.document_scale_prior['log_sd']
        else:
            raise ValueError('Unknown or unavailable source hierarchy interweave level')
        if not len(effect_coordinates):
            raise ValueError('Source hierarchy scale requires at least one governed effect')
        exponent = -log_sd * float(epsilon)
        try:
            multiplier = math.exp(exponent)
        except OverflowError:
            return None
        if not math.isfinite(multiplier) or multiplier == 0.:
            return None
        trial = z.copy()
        trial[scale_coordinate] += epsilon
        trial[effect_coordinates] *= multiplier
        if not np.isfinite(trial).all():
            return None
        old_effects = z[effect_coordinates]
        new_effects = trial[effect_coordinates]
        with np.errstate(over='ignore',invalid='ignore'):
            gaussian_change = -.5 * (
                trial[scale_coordinate] ** 2 - z[scale_coordinate] ** 2
                + float(new_effects @ new_effects - old_effects @ old_effects))
        log_jacobian = -len(effect_coordinates) * log_sd * float(epsilon)
        correction = gaussian_change + log_jacobian
        if not math.isfinite(correction):
            return None
        return dict(state=trial, correction=float(correction),
                    log_jacobian=float(log_jacobian),
                    dimension=int(len(effect_coordinates)))

    def transformed(self, z, *, coordinates_are_local=False):
        """Return spreads, type means, centered residuals and document offsets."""
        z = np.asarray(z, dtype=float)
        def at(coordinate):
            index = self._coordinate_positions[int(coordinate)] if coordinates_are_local else int(coordinate)
            return z[...,index]
        def scale(coordinate, prior):
            # This is the stated smooth lognormal transform.  Non-finite extreme
            # proposals are rejected by the enclosing likelihood rather than
            # silently clipped into a different prior.
            with np.errstate(over='ignore'):
                return prior['median'] * np.exp(prior['log_sd'] * at(coordinate))
        tau_type = scale(self.type_scale_coordinate, self.type_scale_prior)
        leading = z.shape[:-1]
        type_effects = {self.reference_type: np.zeros(leading)}
        for source_type, coordinate in self.type_coordinates.items():
            type_effects[source_type] = tau_type * at(coordinate)
        tau_document = None
        if self.document_scale_coordinate is not None:
            tau_document = scale(self.document_scale_coordinate, self.document_scale_prior)
        residuals = {}
        offsets = {}
        for source_type in self.types:
            documents = self.documents_by_type[source_type]
            if source_type in self.document_coordinates:
                raw = np.stack([at(coordinate) for coordinate in
                                self.document_coordinates[source_type]],axis=-1)
                centered = np.einsum('...k,dk->...d', raw, self.document_bases[source_type])
                centered = centered * tau_document[..., None]
            else:
                centered = np.zeros(leading + (1,))
            for index, document in enumerate(documents):
                residuals[document] = centered[..., index]
                offsets[document] = type_effects[source_type] + centered[..., index]
        return dict(type_scale=tau_type, document_scale=tau_document,
                    type_effects=type_effects, document_residuals=residuals,
                    document_offsets=offsets)

    def offsets_for_sources(self, z, all_source_families):
        transformed = self.transformed(z)
        shape = np.asarray(z).shape[:-1] + (len(all_source_families),)
        result = np.zeros(shape)
        positions = {name: i for i, name in enumerate(all_source_families)}
        for document, values in transformed['document_offsets'].items():
            result[..., positions[document]] = values
        return result

    def document_has_free_offset(self, document):
        source_type=self.document_type[document]
        return (source_type != self.reference_type or
                source_type in self.document_coordinates)

    def report(self, states=None, support=None):
        """Summarize transformed priors/posteriors without claiming identification."""
        support = {} if support is None else dict(support)
        # A fixed local draw is a deterministic numerical summary of the stated
        # transformed prior, never fitted evidence.
        prior_z = np.random.default_rng(20260920).normal(size=(32768,len(self.coordinates)))
        prior = self.transformed(prior_z,coordinates_are_local=True)
        posterior = self.transformed(states) if states is not None else None

        log_float_max = math.log(np.finfo(float).max)
        log_float_tiny = math.log(np.finfo(float).tiny)

        def finite_exp(value):
            value=float(value)
            if value > log_float_max:
                return None
            if value < log_float_tiny:
                return 0.
            return math.exp(value)

        def variance_from_log(log_variance):
            if log_variance == -math.inf:
                return 0.
            return finite_exp(log_variance)

        type_variance_log=(2*math.log(self.type_scale_prior['median'])
                           +2*self.type_scale_prior['log_sd']**2)
        document_variance_log=(2*math.log(self.document_scale_prior['median'])
                               +2*self.document_scale_prior['log_sd']**2)

        def log_distribution(prior_values, posterior_values, log_prior_variance):
            prior_values = np.asarray(prior_values, dtype=float).reshape(-1)
            quantiles=np.quantile(prior_values,[.05,.5,.95])
            analytic_variance=variance_from_log(log_prior_variance)
            out = dict(prior=dict(median=float(quantiles[1]),mean=0.,
                                  ci90=[float(quantiles[0]),float(quantiles[2])]),
                       posterior=None, analytic_prior_variance=analytic_variance,
                       analytic_log_prior_variance=(None if log_prior_variance == -math.inf
                                                    else float(log_prior_variance)),
                       marginal_variance_contraction=None)
            if posterior_values is not None:
                posterior_values = np.asarray(posterior_values, dtype=float).reshape(-1)
                out['posterior'] = summary(posterior_values)
                if analytic_variance not in (None,0.):
                    out['marginal_variance_contraction'] = float(
                        1 - np.var(posterior_values, ddof=1) / analytic_variance)
            return out

        def multiplier_distribution(prior_log_values, posterior_log_values,
                                    log_prior_variance):
            def quantile_summary(values):
                q=np.quantile(np.asarray(values,dtype=float).reshape(-1),[.05,.5,.95])
                converted=[finite_exp(x) for x in q]
                return dict(median=converted[1],mean=None,
                            ci90=[converted[0],converted[2]],
                            log_quantiles=[float(q[0]),float(q[1]),float(q[2])],
                            floating_point_overflow=any(x is None for x in converted))
            degenerate=(log_prior_variance == -math.inf)
            return dict(prior=quantile_summary(prior_log_values),
                posterior=(None if posterior_log_values is None else
                           quantile_summary(posterior_log_values)),
                prior_mean=(1. if degenerate else None),
                prior_variance=(0. if degenerate else None),
                prior_moment_status=('degenerate_multiplier_one' if degenerate else
                    'nonzero_log_offset_has_infinite_multiplier_mean_and_variance'),
                marginal_variance_contraction=None,
                quantiles_computed_by_exponentiating_log_offset_quantiles=True)

        def scale_distribution(prior_values, posterior_values, specification):
            median,log_sd=specification['median'],specification['log_sd']
            log_variance=(2*math.log(median)+log_sd**2
                +math.log(math.expm1(log_sd**2)) if log_sd**2 < 700 else
                2*math.log(median)+2*log_sd**2)
            analytic_variance=variance_from_log(log_variance)
            prior_summary=dict(median=median,
                mean=finite_exp(math.log(median)+log_sd**2/2),
                ci90=[finite_exp(math.log(median)+log_sd*ndtri(.05)),
                      finite_exp(math.log(median)+log_sd*ndtri(.95))])
            out=dict(prior=prior_summary,posterior=None,
                analytic_prior_variance=analytic_variance,
                analytic_log_prior_variance=float(log_variance),
                marginal_variance_contraction=None)
            if posterior_values is not None:
                values=np.asarray(posterior_values,dtype=float).reshape(-1)
                out['posterior']=summary(values)
                if analytic_variance not in (None,0.):
                    out['marginal_variance_contraction']=float(
                        1-np.var(values,ddof=1)/analytic_variance)
            return out

        type_rows = {}
        for source_type in self.types:
            documents = self.documents_by_type[source_type]
            informative = sum(int(support.get(name, 0)) for name in documents)
            positive = sum(bool(support.get(name, 0)) for name in documents)
            values = prior['type_effects'][source_type]
            post = None if posterior is None else posterior['type_effects'][source_type]
            log_variance=(-math.inf if source_type == self.reference_type else type_variance_log)
            type_rows[source_type] = dict(
                documents=list(documents), informative_duration_rows=informative,
                documents_with_informative_rows=positive,
                reference_coordinate_fixed_zero=(source_type == self.reference_type),
                type_log_offset=log_distribution(values, post, log_variance),
                type_multiplier=multiplier_distribution(values,post,log_variance),
                limited_document_contrast_replication=(len(documents) < 2 or positive < 2))
        document_rows = {}
        for document in self.documents:
            residual = prior['document_residuals'][document]
            offset = prior['document_offsets'][document]
            post_residual = None if posterior is None else posterior['document_residuals'][document]
            post_offset = None if posterior is None else posterior['document_offsets'][document]
            source_type=self.document_type[document]
            n=len(self.documents_by_type[source_type])
            residual_log_variance=(-math.inf if n == 1 else
                                   document_variance_log+math.log1p(-1/n))
            type_log_variance=(-math.inf if source_type == self.reference_type else
                               type_variance_log)
            effective_log_variance=float(np.logaddexp(type_log_variance,residual_log_variance))
            document_rows[document] = dict(
                source_type=source_type,
                informative_duration_rows=int(support.get(document, 0)),
                no_direct_duration_support=not bool(support.get(document, 0)),
                document_log_residual=log_distribution(
                    residual,post_residual,residual_log_variance),
                effective_log_offset=log_distribution(
                    offset,post_offset,effective_log_variance),
                effective_multiplier=multiplier_distribution(
                    offset,post_offset,effective_log_variance))
        supported_nonreference = sum(type_rows[name]['informative_duration_rows'] > 0
                                     for name in self.type_coordinates)
        replicated_supported = sum(row['documents_with_informative_rows'] >= 2
                                   for row in type_rows.values())
        scale_rows = dict(
            type=scale_distribution(prior['type_scale'],
                None if posterior is None else posterior['type_scale'],self.type_scale_prior),
            document=(None if prior['document_scale'] is None else scale_distribution(
                prior['document_scale'],None if posterior is None else posterior['document_scale'],
                self.document_scale_prior)))
        measured={
            'scale_parameters': sorted(name for name,row in scale_rows.items()
                if row is not None and row['marginal_variance_contraction'] is not None
                and row['marginal_variance_contraction'] < .25),
            'type_log_offsets': sorted(name for name,row in type_rows.items()
                if row['type_log_offset']['marginal_variance_contraction'] is not None
                and row['type_log_offset']['marginal_variance_contraction'] < .25),
            'document_effective_log_offsets': sorted(name for name,row in document_rows.items()
                if row['effective_log_offset']['marginal_variance_contraction'] is not None
                and row['effective_log_offset']['marginal_variance_contraction'] < .25)}
        result = dict(schema_version='source-offset-hierarchy-report/1', enabled=True,
            reference_type=self.reference_type,
            reference_zero_is_coordinate_convention_not_unbiasedness=True,
            source_family_grouping='document', elapsed_channel_only=True,
            whitened_standard_normal_coordinates=len(self.coordinates),
            deterministic_prior_summary_draws=len(prior_z),
            legacy_fixed_source_sd_used=False,
            type_scale_prior=self.type_scale_prior, document_scale_prior=self.document_scale_prior,
            document_scale_semantics='SD of orthonormal contrast coordinates; each n-document residual has conditional variance tau_document^2*(1-1/n).',
            scale_summaries=scale_rows, source_types=type_rows, documents=document_rows,
            limited_replication_warnings=dict(
                type_scale=('Fewer than two supported nonreference type contrasts.'
                            if supported_nonreference < 2 else None),
                document_scale=('No type has two documents with informative rows.'
                    if self.document_scale_coordinate is None or replicated_supported == 0 else None),
                source_types_without_informative_rows=sorted(name for name, row in type_rows.items()
                                    if name != self.reference_type and not row['informative_duration_rows']),
                document_contrasts_with_limited_replication=sorted(name for name, row in type_rows.items()
                                          if row['limited_document_contrast_replication']),
                qualification='Replication counts are structural warnings, not proof that a scale is or is not learned.'),
            measured_low_marginal_contraction=dict(threshold=.25,**measured,
                qualification='Measured transformed marginal contraction is parameterization-dependent and not identification.'),
            bias_identification_established=False,
            qualifications=[
                'Reference type zero is an anchoring convention, not evidence that the reference is unbiased.',
                'Transformed marginal variance contraction is parameterization-dependent and is not full identification.',
                'The declared type and document exchangeability assumptions are not learned source reliability.',
                'For every nondegenerate lognormal-mixture log offset, the multiplier prior mean and variance are infinite; multiplier means and variance contraction are therefore omitted.',
                'Source-comparison rank is a reduced declared-review screen and cannot certify this hierarchy.',
                'Reporting precision, contamination, selection and document dependence are not adjusted by this bias hierarchy.'])
        if self.reference_histogram_cohorts:
            result['schema_version'] = 'source-offset-hierarchy-report/2'
            result['reference_histogram_support'] = dict(
                anchors=[dict(a) for a in self.reference_histogram_cohorts],
                exact_histogram_factors=len(self.reference_histogram_cohorts),
                recorded_cases=sum(a['sample_size'] for a in self.reference_histogram_cohorts),
                additional_likelihood_factors=0,
                additional_reference_coordinates_allocated=0,
                binding_verified=True,
                substantive_review_verified=False,
                matched_comparison_established=False,
                qualification='Exact-cohort likelihood anchors the model under its declared sampling/count assumptions; no source completeness, unbiasedness, matched population or transport is certified.')
        return result
