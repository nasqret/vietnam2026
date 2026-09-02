"""Working actual-witness bridge for a rightmost-factor append induction.

All products, trailing shifts, scalar outputs, harmless leading paddings and
same-length sums are existing first-order graphs. No new alias, raw beta-code
identity, global associativity theorem, or admission is supplied by this file.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _and, _call, _intro, _lt, _parts, _prime
from peano_lab.library.prime_field_polynomial_candidate import _add, _at, _coeff, _equal, _scale
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution, _length
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent, _left_pad
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _shift(b: str, c: str, length: str, d: str, e: str, tag: str) -> str:
    return _and(_equal(b, c, d, e, length, tag + 'prefix'), _at(d, e, length, '0', tag + 'zero'))


def _aligned(p: str, scalar: str, a: tuple[str, str, str], old: tuple[str, str, str],
             outputs: tuple[str, ...], tag: str) -> tuple[str, ...]:
    ab, ac, length = a
    pb, pc, old_length = old
    ub, uc, vb, vc, UPb, UPc, VPb, VPc, zb, zc = outputs
    return (
        _shift(pb, pc, old_length, ub, uc, tag + 'shift'),
        _scale(p, scalar, ab, ac, vb, vc, length, tag + 'scale'),
        _left_pad(ub, uc, 'S ' + old_length, length, UPb, UPc, tag + 'left'),
        _left_pad(vb, vc, length, 'S ' + old_length, VPb, VPc, tag + 'right'),
        _add(p, UPb, UPc, VPb, VPc, zb, zc, length + '+S ' + old_length, tag + 'sum'),
    )


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join('(' + part + ')' for part in (*premises, result))


A, B, P, Q, R = ('ab','ac','L'), ('bb','bc','M'), ('pb','pc','N'), ('qb','qc','K'), ('rb','rc','T')
LEFT_OUTPUTS = ('ub','uc','vb','vc','UPb','UPc','VPb','VPc','zb','zc')
RIGHT_OUTPUTS = ('eb','ec','fb','fc','EPb','EPc','FPb','FPc','yb','yc')
HELPER_PARAMETERS = ('p','c',*A,*B,*P,*Q,*R,*LEFT_OUTPUTS,'sb','sc','W',*RIGHT_OUTPUTS)
INPUT_LENGTH, OUTPUT_LENGTH = 'M+S K', 'N+S T'


def _aligned_multiplication_row(spec: Callable[..., Any]) -> Any:
    ab = _convolution('p', *A, *B, *P, 'step_helper_AB')
    aq = _convolution('p', *A, *Q, *R, 'step_helper_AQ')
    az = _convolution('p', *A, 'zb', 'zc', INPUT_LENGTH, 'sb', 'sc', 'W', 'step_helper_AZ')
    left = _aligned('p','c',B,Q,LEFT_OUTPUTS,'step_helper_left_')
    right = _aligned('p','c',P,R,RIGHT_OUTPUTS,'step_helper_right_')
    body = _intro(*HELPER_PARAMETERS, 'hp','hAB','hAQ','hU','hV','hUP','hVP','hZ','hAZ','hE','hF','hEP','hFP','hY')
    body += ('have hp0 : ~(p=0)', 'intro hz') + _call('prime_nonzero','p') + ('exact hp','exact hz')
    for label, formula, hypothesis in (('hABcopy',ab,'hAB'),('hAQcopy',aq,'hAQ'),('hAZcopy',az,'hAZ')):
        body += ('have ' + label + ' : ' + formula, 'exact ' + hypothesis) + _parts(label,4)
    scale_bounds = _and(_coeff('p','bb','bc','M','step_helper_B_bound'),
                        _coeff('p','vb','vc','M','step_helper_scaled_B_bound'))
    body += ('have hscale_bounds : ' + scale_bounds,)
    body += _call('prime_field_polynomial_scale_bounded','p','c','bb','bc','vb','vc','M')
    body += ('exact hV','cases hscale_bounds')
    add_bounds = _and(_coeff('p','UPb','UPc',INPUT_LENGTH,'step_helper_input_left_bound'),
                      _coeff('p','VPb','VPc',INPUT_LENGTH,'step_helper_input_right_bound'),
                      _coeff('p','zb','zc',INPUT_LENGTH,'step_helper_input_sum_bound'))
    body += ('have hadd_bounds : ' + add_bounds,)
    body += _call('prime_field_polynomial_add_bounded','p','UPb','UPc','VPb','VPc','zb','zc',INPUT_LENGTH)
    body += ('exact hZ',) + _parts('hadd_bounds',3)

    # Construct the product with the actual shifted Q at its own proper length.
    body += (f"have hlength : exists J. ({_length('L','S K','J','step_helper_shifted_length')})",)
    body += _call('polynomial_product_length_exists','L','S K') + ('cases hlength',)
    shifted_product = _convolution('p',*A,'ub','uc','S K','mb','mc','x','step_helper_shifted_product')
    body += ('have hshifted_product : exists mb mc. ' + shifted_product,)
    body += _call('prime_field_polynomial_convolution_at_length_exists','p',*A,'ub','uc','S K','x')
    body += ('exact hp0','exact hABcopy_left')
    body += _call('prime_field_polynomial_shift_bounded','p','qb','qc','K','ub','uc')
    body += ('exact hp','exact hAQcopy_right_left','exact hU','exact hlength_witness',
             'cases hshifted_product','cases hshifted_product_witness')
    # The scaled B has B's actual length, so the AB product length N is reused.
    scaled_product = _convolution('p',*A,'vb','vc','M','mb','mc','N','step_helper_scaled_product')
    body += ('have hscaled_product : exists mb mc. ' + scaled_product,)
    body += _call('prime_field_polynomial_convolution_at_length_exists','p',*A,'vb','vc','M','N')
    body += ('exact hp0','exact hABcopy_left','exact hscale_bounds_right','exact hABcopy_right_right_left',
             'cases hscaled_product','cases hscaled_product_witness')
    # Both padded factors have the same displayed length; their real products
    # therefore use the proper length W already supplied by the actual A*Z.
    for label, codes, bound in (('hfirst',('UPb','UPc'),'hadd_bounds_left'),
                                ('hsecond',('VPb','VPc'),'hadd_bounds_right_left')):
        product = _convolution('p',*A,*codes,INPUT_LENGTH,'mb','mc','W','step_helper_'+label)
        body += ('have ' + label + ' : exists mb mc. ' + product,)
        body += _call('prime_field_polynomial_convolution_at_length_exists','p',*A,*codes,INPUT_LENGTH,'W')
        body += ('exact hp0','exact hABcopy_left','exact '+bound,'exact hAZcopy_right_right_left',
                 'cases '+label,'cases '+label+'_witness')
    distributed = _add('p','x5','x6','x7','x8','sb','sc','W','step_helper_distributed')
    body += ('have hdistributed : ' + distributed,)
    body += _call('prime_field_polynomial_convolution_left_add',
                  'p','UPb','UPc','VPb','VPc','zb','zc',INPUT_LENGTH,*A,'x5','x6','x7','x8','sb','sc','W')
    body += ('exact hZ','exact hfirst_witness_witness','exact hsecond_witness_witness','exact hAZ')

    # Remove only harmless leading padding, and use actual trailing-shift
    # covariance to compare the first product with the supplied shift of AQ.
    shift_equal = _equivalent('x1','x2','x','eb','ec','S T','step_helper_shift_equal')
    body += ('have hshift_equal : ' + shift_equal,)
    body += _call('prime_field_polynomial_convolution_shift_right_equivalent',
                  'p',*A,*Q,*R,'ub','uc','x1','x2','x','eb','ec')
    body += ('exact hp0','exact hU','exact hAQ','exact hshifted_product_witness_witness','exact hE')
    first_pad = _equivalent('x1','x2','x','x5','x6','W','step_helper_first_pad')
    body += ('have hfirst_pad : ' + first_pad,)
    body += _call('prime_field_polynomial_convolution_left_padding_equivalent_right',
                  'p',*A,'ub','uc','S K','x1','x2','x','UPb','UPc','M','x5','x6','W')
    body += ('exact hp0','exact hUP','exact hshifted_product_witness_witness','exact hfirst_witness_witness')
    first_base = _equivalent('x5','x6','W','eb','ec','S T','step_helper_first_base')
    body += ('have hfirst_base : ' + first_base,)
    body += _call('prime_field_polynomial_equivalent_transitive','x5','x6','W','x1','x2','x','eb','ec','S T')
    body += _call('prime_field_polynomial_equivalent_symmetric','x1','x2','x','x5','x6','W')
    body += ('exact hfirst_pad','exact hshift_equal')
    first_equal = _equivalent('x5','x6','W','EPb','EPc',OUTPUT_LENGTH,'step_helper_first_equal')
    body += ('have hfirst_equal : ' + first_equal,)
    body += _call('prime_field_polynomial_equivalent_transitive','x5','x6','W','eb','ec','S T','EPb','EPc',OUTPUT_LENGTH)
    body += ('exact hfirst_base',) + _call('prime_field_polynomial_left_pad_equivalent','eb','ec','S T','N','EPb','EPc')
    body += ('exact hEP',)

    # Scalar covariance compares actual outputs at N. It does not compare beta
    # codes or assert that the shifted product length is a successor of T.
    scaled_equal = _and('N=N',_equal('x3','x4','fb','fc','N','step_helper_scalar_equal'))
    body += ('have hscaled_equal : ' + scaled_equal,)
    body += _call('prime_field_polynomial_convolution_right_scale_equal',
                  'p','c',*A,*B,'vb','vc',*P,'x3','x4','N','fb','fc')
    body += ('exact hV','exact hAB','exact hscaled_product_witness_witness','exact hF','cases hscaled_equal')
    scalar_base = _equivalent('x3','x4','N','fb','fc','N','step_helper_scalar_base')
    body += ('have hscalar_base : ' + scalar_base,)
    body += _call('prime_field_polynomial_equal_implies_equivalent','x3','x4','fb','fc','N')
    body += ('exact hscaled_equal_right',)
    second_pad = _equivalent('x3','x4','N','x7','x8','W','step_helper_second_pad')
    body += ('have hsecond_pad : ' + second_pad,)
    body += _call('prime_field_polynomial_convolution_left_padding_equivalent_right',
                  'p',*A,'vb','vc','M','x3','x4','N','VPb','VPc','S K','x7','x8','W')
    body += ('exact hp0','exact hVP','exact hscaled_product_witness_witness',
             'have hcomm_input : S K+M=M+S K') + _call('add_comm','S K','M')
    converted = _convolution('p',*A,'VPb','VPc','S K+M','x7','x8','W','step_helper_input_commute')
    body += _rewrite_all('hcomm_input',converted,'S K+M') + ('exact hsecond_witness_witness',)
    second_base = _equivalent('x7','x8','W','fb','fc','N','step_helper_second_base')
    body += ('have hsecond_base : ' + second_base,)
    body += _call('prime_field_polynomial_equivalent_transitive','x7','x8','W','x3','x4','N','fb','fc','N')
    body += _call('prime_field_polynomial_equivalent_symmetric','x3','x4','N','x7','x8','W')
    body += ('exact hsecond_pad','exact hscalar_base')
    second_equal = _equivalent('x7','x8','W','FPb','FPc',OUTPUT_LENGTH,'step_helper_second_equal')
    body += ('have hsecond_equal : ' + second_equal,)
    body += _call('prime_field_polynomial_equivalent_transitive','x7','x8','W','fb','fc','N','FPb','FPc',OUTPUT_LENGTH)
    body += ('exact hsecond_base',)
    output_pad = _equivalent('fb','fc','N','FPb','FPc','S T+N','step_helper_output_commute')
    body += ('have houtput_pad : ' + output_pad,)
    body += _call('prime_field_polynomial_left_pad_equivalent','fb','fc','N','S T','FPb','FPc') + ('exact hFP',)
    body += ('have hcomm_output : S T+N=N+S T',) + _call('add_comm','S T','N')
    body += _rewrite_all('hcomm_output',output_pad,'S T+N','houtput_pad') + ('exact houtput_pad',)
    body += _call('prime_field_polynomial_add_equivalent_congruent',
                  'p','x5','x6','x7','x8','sb','sc','W','EPb','EPc','FPb','FPc','yb','yc',OUTPUT_LENGTH)
    body += ('exact hp','exact hfirst_equal','exact hsecond_equal','exact hdistributed','exact hY')
    return spec(
        'prime_field_polynomial_convolution_shift_scale_aligned_equivalent',
        _contract(HELPER_PARAMETERS,(_prime('p','step_helper_prime'),ab,aq,*left,az,*right),
                  _equivalent('sb','sc','W','yb','yc',OUTPUT_LENGTH,'step_helper_result')),
        ('prime_nonzero','prime_field_polynomial_scale_bounded','prime_field_polynomial_add_bounded',
         'polynomial_product_length_exists','prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_shift_bounded','prime_field_polynomial_convolution_left_add',
         'prime_field_polynomial_convolution_shift_right_equivalent',
         'prime_field_polynomial_convolution_left_padding_equivalent_right',
         'prime_field_polynomial_equivalent_transitive','prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_left_pad_equivalent','prime_field_polynomial_convolution_right_scale_equal',
         'prime_field_polynomial_equal_implies_equivalent','add_comm','prime_field_polynomial_add_equivalent_congruent'),
        body,
        'For actual AB and AQ, multiplying an actual leading-pad-aligned sum XQ+cB by A is formally equivalent to every actual aligned sum X(AQ)+c(AB). All four intermediate products are genuinely constructed, scalar and shift outputs remain actual graph witnesses, proper product lengths are independent, and no associativity hypothesis or output equality is assumed.',
    )


OLD0, OLD1 = ('b0','c0','N0'), ('b1','c1','N1')
ALIGN0 = ('u0b','u0c','v0b','v0c','UP0b','UP0c','VP0b','VP0c','z0b','z0c')
ALIGN1 = ('u1b','u1c','v1b','v1c','UP1b','UP1c','VP1b','VP1c','z1b','z1c')
COMPARISON_PARAMETERS = ('p','c',*A,*OLD0,*OLD1,*ALIGN0,*ALIGN1)


def _aligned_congruence_row(spec: Callable[..., Any]) -> Any:
    old_equal = _equivalent(*OLD0,*OLD1,'step_alignment_old_equal')
    old_alignment = _aligned('p','c',A,OLD0,ALIGN0,'step_alignment_old_')
    new_alignment = _aligned('p','c',A,OLD1,ALIGN1,'step_alignment_new_')
    g0,g1 = 'L+S N0','L+S N1'
    body = _intro(*COMPARISON_PARAMETERS,'hp','he','hU0','hV0','hUP0','hVP0','hZ0',
                  'hU1','hV1','hUP1','hVP1','hZ1')
    shifted = _equivalent('u0b','u0c','S N0','u1b','u1c','S N1','step_alignment_shifted')
    body += ('have hshifted : ' + shifted,)
    body += _call('prime_field_polynomial_shift_equivalent_congruent',*OLD0,*OLD1,'u0b','u0c','u1b','u1c')
    body += ('exact he','exact hU0','exact hU1')
    scaled = _equal('v0b','v0c','v1b','v1c','L','step_alignment_scaled')
    body += ('have hscaled : ' + scaled,)
    body += _call('prime_field_polynomial_scale_functional','p','c','ab','ac','v0b','v0c','v1b','v1c','L')
    body += ('exact hV0','exact hV1')
    scalar_equal = _equivalent('v0b','v0c','L','v1b','v1c','L','step_alignment_scalar_equal')
    body += ('have hscalar_equal : ' + scalar_equal,)
    body += _call('prime_field_polynomial_equal_implies_equivalent','v0b','v0c','v1b','v1c','L')
    body += ('exact hscaled',)
    for label,source,count,target,hypothesis,common in (
        ('left0',('u0b','u0c','S N0'),'L',('UP0b','UP0c'),'hUP0',g0),
        ('left1',('u1b','u1c','S N1'),'L',('UP1b','UP1c'),'hUP1',g1),
        ('right0',('v0b','v0c','L'),'S N0',('VP0b','VP0c'),'hVP0',g0),
        ('right1',('v1b','v1c','L'),'S N1',('VP1b','VP1c'),'hVP1',g1),
    ):
        raw = count+'+'+source[2]
        equality = _equivalent(*source,*target,raw,'step_alignment_pad_'+label)
        body += ('have hpad_'+label+' : '+equality,)
        body += _call('prime_field_polynomial_left_pad_equivalent',*source,count,*target) + ('exact '+hypothesis,)
        if raw != common:
            body += ('have hcomm_'+label+' : '+raw+'='+common,) + _call('add_comm',count,source[2])
            body += _rewrite_all('hcomm_'+label,equality,raw,'hpad_'+label)
    for side,source0,source1,target0,target1,between in (
        ('left',('u0b','u0c','S N0'),('u1b','u1c','S N1'),('UP0b','UP0c'),('UP1b','UP1c'),'hshifted'),
        ('right',('v0b','v0c','L'),('v1b','v1c','L'),('VP0b','VP0c'),('VP1b','VP1c'),'hscalar_equal'),
    ):
        middle = _equivalent(*target0,g0,*source1,'step_alignment_middle_'+side)
        body += ('have hmiddle_'+side+' : '+middle,)
        body += _call('prime_field_polynomial_equivalent_transitive',*target0,g0,*source0,*source1)
        body += _call('prime_field_polynomial_equivalent_symmetric',*source0,*target0,g0)
        body += ('exact hpad_'+side+'0','exact '+between)
        equality = _equivalent(*target0,g0,*target1,g1,'step_alignment_result_'+side)
        body += ('have hequal_'+side+' : '+equality,)
        body += _call('prime_field_polynomial_equivalent_transitive',*target0,g0,*source1,*target1,g1)
        body += ('exact hmiddle_'+side,'exact hpad_'+side+'1')
    body += _call('prime_field_polynomial_add_equivalent_congruent',
                  'p','UP0b','UP0c','VP0b','VP0c','z0b','z0c',g0,
                  'UP1b','UP1c','VP1b','VP1c','z1b','z1c',g1)
    body += ('exact hp','exact hequal_left','exact hequal_right','exact hZ0','exact hZ1')
    return spec(
        'prime_field_polynomial_shift_scale_aligned_congruent',
        _contract(COMPARISON_PARAMETERS,(_prime('p','step_alignment_prime'),old_equal,*old_alignment,*new_alignment),
                  _equivalent('z0b','z0c',g0,'z1b','z1c',g1,'step_alignment_result')),
        ('prime_field_polynomial_shift_equivalent_congruent','prime_field_polynomial_scale_functional',
         'prime_field_polynomial_equal_implies_equivalent','prime_field_polynomial_left_pad_equivalent',
         'add_comm','prime_field_polynomial_equivalent_transitive','prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_add_equivalent_congruent'),
        body,
        'Formal equivalence of two old prefixes preserves every actual aligned sum of their trailing-zero shifts with a fixed actual scalar multiple of the same source. Both old lengths, all shift/scale encodings, both leading paddings and the sum encodings remain independent; only formal output coefficients are concluded equal.',
    )


C = ('cb','cc','J')
Q0, R0, S0 = ('q0b','q0c','K0'), ('r0b','r0c','U0'), ('s0b','s0c','V0')
Q1, R1, S1 = ('q1b','q1c','K1'), ('r1b','r1c','U1'), ('s1b','s1c','V1')
STEP_PARAMETERS = ('p',*A,*B,*P,*C,*Q0,*R0,*S0,'c','db','dc',*Q1,*R1,*S1)


def _fresh(index: int) -> str:
    return 'x' if index == 0 else 'x'+str(index)


def _conjunction_parts(hypothesis: str, count: int) -> tuple[str, ...]:
    return tuple(hypothesis+'_right'*index+'_left' for index in range(count-1)) + (hypothesis+'_right'*(count-1),)


def _append_step_row(spec: Callable[..., Any]) -> Any:
    ab = _convolution('p',*A,*B,*P,'append_step_AB')
    q0 = _convolution('p',*B,*C,*Q0,'append_step_Q0')
    r0 = _convolution('p',*P,*C,*R0,'append_step_R0')
    s0 = _convolution('p',*A,*Q0,*S0,'append_step_S0')
    induction = _equivalent(*R0,*S0,'append_step_actual_induction_hypothesis')
    copied = _equal('cb','cc','db','dc','J','append_step_prefix')
    last = _at('db','dc','J','c','append_step_last')
    d = ('db','dc','S J')
    q1 = _convolution('p',*B,*d,*Q1,'append_step_Q1')
    r1 = _convolution('p',*P,*d,*R1,'append_step_R1')
    s1 = _convolution('p',*A,*Q1,*S1,'append_step_S1')
    body = _intro(*STEP_PARAMETERS,'hp','hAB','hQ0','hR0','hS0','hIH','hprefix','hlast','hQ1','hR1','hS1')
    body += ('have hp0 : ~(p=0)','intro hz') + _call('prime_nonzero','p') + ('exact hp','exact hz')
    body += ('have hABcopy : '+ab,'exact hAB') + _parts('hABcopy',4)
    body += ('have hQ1copy : '+q1,'exact hQ1') + _parts('hQ1copy',4)
    # Even an empty B gives a real bounded D in the actual B*D graph.
    # Its actual endpoint therefore supplies c<p without an extra premise.
    body += (f"have hc : {_lt('c','p','append_step_scalar_bound')}",)
    body += _call('matrix_rank_bounded_prefix_value','db','dc','S J','p','J','c')
    body += ('exact hQ1copy_right_left',) + _call('le_refl','S J') + ('exact hlast',)
    for label,first,second,output,hypothesis in (
        ('hPbound',A,B,P,'hAB'),('hQ0bound',B,C,Q0,'hQ0'),
        ('hR0bound',P,C,R0,'hR0'),('hS0bound',A,Q0,S0,'hS0'),
    ):
        bound = _coeff('p',*output,'append_step_'+label)
        body += ('have '+label+' : '+bound,)
        body += _call('prime_field_polynomial_convolution_bounded','p',*first,*second,*output)
        body += ('exact '+hypothesis,)

    def construct_alignment(label,source,old,source_bound,old_bound,offset):
        data = _and(*_aligned('p','c',source,old,LEFT_OUTPUTS,'append_step_'+label+'_'))
        commands = ('have '+label+' : exists '+' '.join(LEFT_OUTPUTS)+'. '+data,)
        commands += _call('prime_field_polynomial_shift_scale_aligned_sum_exists','p','c',*source,*old)
        commands += ('exact hp','exact hc','exact '+source_bound,'exact '+old_bound)
        commands += tuple('cases '+label+'_witness'*index for index in range(10))
        witness = label+'_witness'*10
        commands += _parts(witness,5)
        return commands,tuple(_fresh(offset+index) for index in range(10)),_conjunction_parts(witness,5)

    # Only Y is shared by the two branches. Each branch constructs its own
    # remaining witnesses inside a local fact and discharges them before the
    # other branch begins. This is ordinary eigenvariable scope discipline,
    # not a change to any constructor, statement or compiler depth guard.
    commands,y,yparts = construct_alignment('hYalign',P,S0,'hPbound','hS0bound',0)
    body += commands
    hz,hy,hy0 = 'M+S K0','N+S V0','N+S U0'
    s_total = _equivalent(*S1,y[8],y[9],hy,'append_step_S_total')
    body += ('have hS_total : '+s_total,)
    commands,z,zparts = construct_alignment('hZalign',B,Q0,'hABcopy_right_left','hQ0bound',10)
    body += commands
    bounds = _and(_coeff('p',z[4],z[5],hz,'append_step_Z_left_bound'),
                  _coeff('p',z[6],z[7],hz,'append_step_Z_right_bound'),
                  _coeff('p',z[8],z[9],hz,'append_step_Z_output_bound'))
    body += ('have hZbounds : '+bounds,)
    body += _call('prime_field_polynomial_add_bounded','p',*z[4:10],hz)
    body += ('exact '+zparts[4],) + _parts('hZbounds',3)
    body += (f"have hZlength : exists W. ({_length('L',hz,'W','append_step_intermediate_length')})",)
    body += _call('polynomial_product_length_exists','L',hz) + ('cases hZlength',)
    az = _convolution('p',*A,z[8],z[9],hz,'mb','mc','x20','append_step_AZ')
    body += ('have hAZ : exists mb mc. '+az,)
    body += _call('prime_field_polynomial_convolution_at_length_exists','p',*A,z[8],z[9],hz,'x20')
    body += ('exact hp0','exact hABcopy_left','exact hZbounds_right_right','exact hZlength_witness',
             'cases hAZ','cases hAZ_witness')
    helper_equal = _equivalent('x21','x22','x20',y[8],y[9],hy,'append_step_helper_equal')
    body += ('have hhelper_equal : '+helper_equal,)
    body += _call('prime_field_polynomial_convolution_shift_scale_aligned_equivalent',
                  'p','c',*A,*B,*P,*Q0,*S0,*z,'x21','x22','x20',*y)
    body += ('exact hp','exact hAB','exact hS0') + tuple('exact '+name for name in zparts)
    body += ('exact hAZ_witness_witness',) + tuple('exact '+name for name in yparts)

    # Rewrite the actual B*D only by formal equivalence, then transport it
    # through the two real products by A. No arbitrary replacement is assumed.
    q_append = _equivalent(*Q1,z[8],z[9],hz,'append_step_Q_append')
    body += ('have hQ_append : '+q_append,)
    body += _call('prime_field_polynomial_convolution_right_append_equivalent',
                  'p',*B,*C,'c','db','dc',*Q0,*Q1,*z)
    body += ('exact hp','exact hprefix','exact hlast','exact hQ0','exact hQ1')
    body += tuple('exact '+name for name in zparts)
    s_transport = _equivalent(*S1,'x21','x22','x20','append_step_S_transport')
    body += ('have hS_transport : '+s_transport,)
    body += _call('prime_field_polynomial_convolution_equivalent_congruent_right',
                  'p',*A,*Q1,*S1,z[8],z[9],hz,'x21','x22','x20')
    body += ('exact hp0','exact hQ_append','exact hS1','exact hAZ_witness_witness')
    body += _call('prime_field_polynomial_equivalent_transitive',*S1,'x21','x22','x20',y[8],y[9],hy)
    body += ('exact hS_transport','exact hhelper_equal')

    # The S branch has closed: x10..x22 are no longer eigenvariables in
    # scope. The independent R branch may therefore use fresh x10..x19.
    r_total = _equivalent(*R1,y[8],y[9],hy,'append_step_R_total')
    body += ('have hR_total : '+r_total,)
    commands,y0,y0parts = construct_alignment('hY0align',P,R0,'hPbound','hR0bound',10)
    body += commands
    r_append = _equivalent(*R1,y0[8],y0[9],hy0,'append_step_R_append')
    body += ('have hR_append : '+r_append,)
    body += _call('prime_field_polynomial_convolution_right_append_equivalent',
                  'p',*P,*C,'c','db','dc',*R0,*R1,*y0)
    body += ('exact hp','exact hprefix','exact hlast','exact hR0','exact hR1')
    body += tuple('exact '+name for name in y0parts)
    aligned_equal = _equivalent(y0[8],y0[9],hy0,y[8],y[9],hy,'append_step_aligned_induction')
    body += ('have haligned_equal : '+aligned_equal,)
    body += _call('prime_field_polynomial_shift_scale_aligned_congruent','p','c',*P,*R0,*S0,*y0,*y)
    body += ('exact hp','exact hIH') + tuple('exact '+name for name in y0parts+yparts)
    body += _call('prime_field_polynomial_equivalent_transitive',*R1,y0[8],y0[9],hy0,y[8],y[9],hy)
    body += ('exact hR_append','exact haligned_equal')
    body += _call('prime_field_polynomial_equivalent_transitive',*R1,y[8],y[9],hy,*S1)
    body += ('exact hR_total',)
    body += _call('prime_field_polynomial_equivalent_symmetric',*S1,y[8],y[9],hy) + ('exact hS_total',)
    return spec(
        'prime_field_polynomial_convolution_associativity_append_step',
        _contract(STEP_PARAMETERS,(_prime('p','append_step_prime'),ab,q0,r0,s0,induction,copied,last,q1,r1,s1),
                  _equivalent(*R1,*S1,'append_step_result')),
        ('prime_nonzero','matrix_rank_bounded_prefix_value','le_refl','prime_field_polynomial_convolution_bounded',
         'prime_field_polynomial_shift_scale_aligned_sum_exists','prime_field_polynomial_add_bounded',
         'polynomial_product_length_exists','prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_convolution_shift_scale_aligned_equivalent',
         'prime_field_polynomial_convolution_right_append_equivalent',
         'prime_field_polynomial_convolution_equivalent_congruent_right',
         'prime_field_polynomial_equivalent_transitive','prime_field_polynomial_shift_scale_aligned_congruent',
         'prime_field_polynomial_equivalent_symmetric'),
        body,
        'An actual formal-coefficient associativity hypothesis for one rightmost prefix extends through one genuine appended coefficient. Every old and new product is an actual proper-length convolution; the proof derives the canonical appended coefficient bound, constructs three real shift/scale/pad/add alignments and a real intermediate product, and concludes only the next formal equivalence. Empty factors are retained, no successor product-length identity is assumed, and the induction step alone is not full associativity.',
    )


def make_prime_field_polynomial_associativity_step_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_aligned_multiplication_row(spec), _aligned_congruence_row(spec), _append_step_row(spec))


__all__ = ['make_prime_field_polynomial_associativity_step_candidate_theorems']
