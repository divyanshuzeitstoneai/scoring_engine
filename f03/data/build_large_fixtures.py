import json, os, sys, time, datetime, random
from decimal import ROUND_HALF_UP, Decimal
from collections import Counter

SEED = 20260924
random.seed(SEED)

TARGET_TOTAL      = 50_000
BASELINE_NORMAL   = 44_350
BASELINE_FILTERED =  3_000
EDGE_CASE_ORDERS  =  2_650

VOIDED_COUNT        = 1_200
PENDING_COUNT       =   900
TEST_COUNT          =   450
CANCELLED_PREFULFIL =   450

EDGE_DIST = {
    'null_cogs':150,'shipping_lag':150,'gateway_fee_missing':150,
    'discount_code':150,'stacked_discount':150,'sales_tax_embedded':150,
    'partial_refund':150,'full_refund_concession':150,'full_refund_restocked':150,
    'damaged_return':100,'split_tender':100,'pos_channel':100,
    'boundary_zero':100,'boundary_negative_cent':100,'multiline_shipping':100,
    'bundle':100,'historical_drift':100,'timezone_rollup':100,
    'cancelled_partial_ship':100,'promotional':100,'international_shipping':100,
    'loss_leader':100,
}

assert sum(EDGE_DIST.values()) == EDGE_CASE_ORDERS, sum(EDGE_DIST.values())
assert BASELINE_NORMAL + BASELINE_FILTERED + EDGE_CASE_ORDERS == TARGET_TOTAL

GATEWAY_RATES = {
    'shopify_payments': Decimal('0.029'),
    'paypal':           Decimal('0.0349'),
    'stripe':           Decimal('0.029'),
    'amazon_pay':       Decimal('0.04'),
    'afterpay':         Decimal('0.06'),
}
GATEWAY_FIXED = {
    'shopify_payments': Decimal('0.30'),
    'paypal':           Decimal('0.49'),
    'stripe':           Decimal('0.30'),
    'amazon_pay':       Decimal('0.30'),
    'afterpay':         Decimal('0.30'),
}
SHIPPING_BANDS = [
    (Decimal('4.50'), Decimal('7.00')),
    (Decimal('7.00'), Decimal('11.00')),
    (Decimal('11.00'), Decimal('18.00')),
    (Decimal('18.00'), Decimal('35.00')),
]
CATALOG = [
    {'sku':'APP-TEE-S',   'price':Decimal('29.99'), 'cogs_frac':Decimal('0.38')},
    {'sku':'APP-TEE-M',   'price':Decimal('29.99'), 'cogs_frac':Decimal('0.38')},
    {'sku':'APP-TEE-L',   'price':Decimal('29.99'), 'cogs_frac':Decimal('0.38')},
    {'sku':'APP-HOODIE',  'price':Decimal('59.99'), 'cogs_frac':Decimal('0.40')},
    {'sku':'APP-JOGGER',  'price':Decimal('49.99'), 'cogs_frac':Decimal('0.42')},
    {'sku':'APP-HAT',     'price':Decimal('24.99'), 'cogs_frac':Decimal('0.35')},
    {'sku':'HOM-MUG',     'price':Decimal('19.99'), 'cogs_frac':Decimal('0.45')},
    {'sku':'HOM-CANDLE',  'price':Decimal('34.99'), 'cogs_frac':Decimal('0.42')},
    {'sku':'HOM-TRAY',    'price':Decimal('44.99'), 'cogs_frac':Decimal('0.55')},
    {'sku':'HOM-PILLOW',  'price':Decimal('54.99'), 'cogs_frac':Decimal('0.48')},
    {'sku':'ELC-CABLE',   'price':Decimal('14.99'), 'cogs_frac':Decimal('0.62')},
    {'sku':'ELC-CHARGER', 'price':Decimal('24.99'), 'cogs_frac':Decimal('0.65')},
    {'sku':'ELC-CASE',    'price':Decimal('19.99'), 'cogs_frac':Decimal('0.58')},
    {'sku':'BTY-SERUM',   'price':Decimal('49.99'), 'cogs_frac':Decimal('0.30')},
    {'sku':'BTY-CREAM',   'price':Decimal('39.99'), 'cogs_frac':Decimal('0.32')},
    {'sku':'ELC-HEADSET', 'price':Decimal('89.99'), 'cogs_frac':Decimal('0.78')},
    {'sku':'HOM-LAMP',    'price':Decimal('74.99'), 'cogs_frac':Decimal('0.72')},
]
DISCOUNT_CODES = ['WELCOME10','SAVE15','FLASH20','VIP25','FREESHIP','BOGO50']

def _c(v): return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
def _s(v): return str(_c(v))
def _rd(lo, hi): return _c(Decimal(str(random.uniform(lo, hi))))
def _oid(n): return 'gid://shopify/Order/' + str(8_000_000_000 + n)
def _oname(n): return '#' + str(1000 + n)
def _vid(b): return 'gid://shopify/ProductVariant/' + str(9_000_000_000 + b)
def _lid(b): return 'gid://shopify/LineItem/' + str(7_000_000_000 + b)
def _tid(n): return 'gid://shopify/OrderTransaction/' + str(5_000_000_000 + n)

def _gw_fee(rev, gw):
    r = GATEWAY_RATES.get(gw, Decimal('0.029'))
    f = GATEWAY_FIXED.get(gw, Decimal('0.30'))
    return _c(rev * r + f)

def _pick_gw():
    return random.choices(list(GATEWAY_RATES.keys()), weights=[55,20,15,7,3], k=1)[0]

def _pick_ship(band=None):
    if band is None:
        band = random.choices([0,1,2,3], weights=[40,35,18,7], k=1)[0]
    lo, hi = SHIPPING_BANDS[band]
    return _rd(float(lo), float(hi))

def _rdate():
    ts = random.randint(1_704_067_200, 1_756_684_800)
    dt = datetime.datetime.utcfromtimestamp(ts)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

def _make_line(seq, product, qty=1, disc=None, cogs_ov=None, null_cogs=False, bundle=None):
    if disc is None: disc = Decimal('0')
    up = product['price']
    dup = _c(up * (Decimal('1') - disc))
    rev = _c(dup * qty)
    if null_cogs:
        cogs = Decimal('0'); mis = True; inv = {'unitCost': None}
    elif bundle:
        bc = sum(Decimal(str(c['unit_cost'])) * c['qty'] for c in bundle)
        cogs = _c(bc * qty); mis = False
        inv = {'unitCost': {'amount': _s(bc)},
               'metafields': [{'namespace':'custom','key':'bundle_components',
                                'value': json.dumps([{'unit_cost':c['unit_cost'],'quantity':c['qty']} for c in bundle])}]}
    elif cogs_ov is not None:
        cogs = _c(cogs_ov * qty); mis = False; inv = {'unitCost': {'amount': _s(cogs_ov)}}
    else:
        uc = _c(product['cogs_frac'] * up)
        cogs = _c(uc * qty); mis = False; inv = {'unitCost': {'amount': _s(uc)}}
    line = {'id': _lid(seq), 'currentQuantity': qty,
            'discountedUnitPriceSet': {'shopMoney': {'amount': _s(dup)}},
            'variant': {'id': _vid(seq), 'sku': product['sku'], 'inventoryItem': inv},
            'taxLines': []}
    return line, rev, cogs, mis

def _txn(seq, gw, fee):
    return {'id': _tid(seq), 'kind': 'SALE', 'status': 'SUCCESS', 'gateway': gw,
            'fees': [{'amount': {'amount': _s(fee)}}]}

def _refund_txn(seq, amt):
    return {'id': _tid(seq), 'kind': 'REFUND', 'status': 'SUCCESS', 'gateway': 'shopify_payments',
            'fees': [], 'amountSet': {'shopMoney': {'amount': _s(amt)}}}

def _wrap(n, lines, gw, fee, ship_rev, fin, cat, at=None, cancelled=None, tags=None,
          test=False, tax_inc=False, extra_txn=None, ext=None, snap=None):
    txns = [_txn(n, gw, fee)]
    if extra_txn: txns.extend(extra_txn)
    order = {'id': _oid(n), 'name': _oname(n), 'processedAt': at or _rdate(),
             'cancelledAt': cancelled, 'displayFinancialStatus': fin,
             'taxesIncluded': tax_inc, 'currencyCode': 'USD',
             'test': test, 'tags': tags or [], 'paymentGatewayNames': [gw],
             'lineItems': lines,
             'shippingLines': [{'discountedPriceSet': {'shopMoney': {'amount': _s(ship_rev)}}}],
             'transactions': txns}
    return {'order_seq': n, 'category': cat, 'shopify_order_payload': order,
            'external_data': ext or {}, 'cogs_snapshot_table_entry': snap}

def build_baseline(start):
    orders = []; seq = start
    stats = {'breach':0,'no_breach':0,'full_ref':0,'part_ref':0}
    for i in range(BASELINE_NORMAL):
        gw = _pick_gw(); roll = random.random()
        if Decimal(str(roll)) < Decimal('0.06'):
            p = random.choice([CATALOG[10],CATALOG[11],CATALOG[15],CATALOG[16]])
        else:
            p = random.choice(CATALOG)
        qty = random.choices([1,2,3,4], weights=[60,25,10,5], k=1)[0]
        line, rev, cogs, _ = _make_line(seq*100, p, qty)
        sc = _pick_ship(); fee = _gw_fee(rev, gw)
        gp = _c(rev - cogs - sc - fee)
        r2 = random.random()
        if r2 < 0.04:
            stats['full_ref'] += 1
            rtx = _refund_txn(seq*100+1, rev)
            w = _wrap(seq,[line],gw,fee,Decimal('0'),'REFUNDED','baseline_refunded',
                      extra_txn=[rtx], ext={'actual_3pl_shipping_invoice':float(sc)})
        elif r2 < 0.09:
            stats['part_ref'] += 1
            ra = _c(rev * _rd(0.2,0.6)); rtx = _refund_txn(seq*100+1, ra)
            w = _wrap(seq,[line],gw,fee,Decimal('0'),'PARTIALLY_REFUNDED','baseline_partial_refund',
                      extra_txn=[rtx], ext={'actual_3pl_shipping_invoice':float(sc),'refund_amount':float(ra)})
        else:
            w = _wrap(seq,[line],gw,fee,Decimal('0'),'PAID','baseline_paid',
                      ext={'actual_3pl_shipping_invoice':float(sc)})
        if gp < Decimal('0'): stats['breach'] += 1
        else: stats['no_breach'] += 1
        orders.append(w); seq += 1
    return orders, seq, stats

def build_filtered(start):
    orders = []; seq = start
    specs = [('VOIDED',VOIDED_COUNT,'filtered_voided'),
             ('PENDING',PENDING_COUNT,'filtered_pending'),
             ('PAID',TEST_COUNT,'filtered_test'),
             ('PAID',CANCELLED_PREFULFIL,'filtered_cancelled')]
    for fin, cnt, cat in specs:
        for _ in range(cnt):
            p = random.choice(CATALOG); line,rev,_,_ = _make_line(seq*100, p)
            gw = _pick_gw(); fee = _gw_fee(rev,gw); sc = _pick_ship(0)
            is_test = (cat == 'filtered_test')
            can = _rdate() if cat == 'filtered_cancelled' else None
            orders.append(_wrap(seq,[line],gw,fee,Decimal('0'),fin,cat,cancelled=can,
                                test=is_test,ext={'actual_3pl_shipping_invoice':float(sc)}))
            seq += 1
    return orders, seq

def e_null_cogs(seq,idx):
    p1,p2 = random.choice(CATALOG[:10]),random.choice(CATALOG[10:])
    l1,r1,_,_ = _make_line(seq*100,p1); l2,r2,_,_ = _make_line(seq*100+1,p2,null_cogs=True)
    gw = _pick_gw(); fee = _gw_fee(r1+r2,gw); sc = _pick_ship(1)
    return _wrap(seq,[l1,l2],gw,fee,Decimal('0'),'PAID','null_cogs',
                 ext={'actual_3pl_shipping_invoice':float(sc)})

def e_ship_lag(seq,idx):
    p = random.choice(CATALOG); qty = random.randint(1,2)
    l,r,_,_ = _make_line(seq*100,p,qty=qty); gw = _pick_gw(); fee = _gw_fee(r,gw)
    sc = _pick_ship(3 if idx%5==0 else random.randint(0,2))
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','shipping_lag',
                 ext={'actual_3pl_shipping_invoice':float(sc),'is_shipping_estimated':True})

def e_gw_missing(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p)
    gw = 'amazon_pay'; sc = _pick_ship(1)
    order = {'id':_oid(seq),'name':_oname(seq),'processedAt':_rdate(),'cancelledAt':None,
             'displayFinancialStatus':'PAID','taxesIncluded':False,'currencyCode':'USD',
             'test':False,'tags':[],'paymentGatewayNames':[gw],'lineItems':[l],
             'shippingLines':[{'discountedPriceSet':{'shopMoney':{'amount':'0.00'}}}],
             'transactions':[{'id':_tid(seq),'kind':'SALE','status':'SUCCESS','gateway':gw,'fees':[]}]}
    return {'order_seq':seq,'category':'gateway_fee_missing','shopify_order_payload':order,
            'external_data':{'actual_3pl_shipping_invoice':float(sc)},'cogs_snapshot_table_entry':None}

def e_disc_code(seq,idx):
    p = random.choice(CATALOG); d = random.choice([Decimal('0.10'),Decimal('0.15'),Decimal('0.20')])
    l,r,_,_ = _make_line(seq*100,p,disc=d); gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(0)
    code = random.choice(DISCOUNT_CODES)
    w = _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','discount_code',
              ext={'actual_3pl_shipping_invoice':float(sc),'discount_code':code})
    w['shopify_order_payload']['discountCodes'] = [{'code':code}]; return w

def e_stacked(seq,idx):
    p = random.choice(CATALOG); a = Decimal('0.10'); c = Decimal('0.15')
    eff = Decimal('1')-(Decimal('1')-a)*(Decimal('1')-c)
    l,r,_,_ = _make_line(seq*100,p,disc=eff); gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(1)
    code = random.choice(DISCOUNT_CODES)
    w = _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','stacked_discount',
              ext={'actual_3pl_shipping_invoice':float(sc),'discount_code':code,'effective_discount_fraction':float(eff)})
    w['shopify_order_payload']['discountCodes'] = [{'code':code}]; return w

def e_tax(seq,idx):
    p = random.choice(CATALOG); tr = Decimal('0.08'); gp = p['price']
    l,r,_,_ = _make_line(seq*100,p); l['discountedUnitPriceSet']['shopMoney']['amount'] = _s(gp)
    gw = _pick_gw(); fee = _gw_fee(gp,gw); sc = _pick_ship(0)
    order = {'id':_oid(seq),'name':_oname(seq),'processedAt':_rdate(),'cancelledAt':None,
             'displayFinancialStatus':'PAID','taxesIncluded':True,'currencyCode':'USD',
             'test':False,'tags':[],'paymentGatewayNames':[gw],'lineItems':[l],
             'shippingLines':[{'discountedPriceSet':{'shopMoney':{'amount':'0.00'}}}],
             'transactions':[_txn(seq,gw,fee)]}
    return {'order_seq':seq,'category':'sales_tax_embedded','shopify_order_payload':order,
            'external_data':{'actual_3pl_shipping_invoice':float(sc),'tax_rate':float(tr)},
            'cogs_snapshot_table_entry':None}

def e_part_ref(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p,qty=2)
    gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(1)
    rf = random.choice([Decimal('0.25'),Decimal('0.50')]); ra = _c(r*rf)
    rtx = _refund_txn(seq*100+1, ra)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PARTIALLY_REFUNDED','partial_refund',
                 extra_txn=[rtx], ext={'actual_3pl_shipping_invoice':float(sc),'refund_amount':float(ra)})

def e_full_conc(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p)
    gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(1)
    rtx = _refund_txn(seq*100+1, r)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'REFUNDED','full_refund_concession',
                 extra_txn=[rtx], ext={'actual_3pl_shipping_invoice':float(sc),'restocked':False})

def e_full_rest(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p)
    gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(1)
    rtx = _refund_txn(seq*100+1, r)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'REFUNDED','full_refund_restocked',
                 extra_txn=[rtx], ext={'actual_3pl_shipping_invoice':float(sc),'restocked':True})

def e_damaged(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p)
    gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(1)
    rtx = _refund_txn(seq*100+1, r)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'REFUNDED','damaged_return',
                 extra_txn=[rtx], ext={'actual_3pl_shipping_invoice':float(sc),'restocked':False,
                                       'damage_cogs_recovery_fraction':0.3})

def e_split(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p)
    sc = _pick_ship(0); gc = _c(r*Decimal('0.4')); cc = r-gc; fee = _gw_fee(cc,'shopify_payments')
    gc_t = {'id':_tid(seq*100+2),'kind':'SALE','status':'SUCCESS','gateway':'gift_card','fees':[]}
    cc_t = _txn(seq*100+3,'shopify_payments',fee)
    order = {'id':_oid(seq),'name':_oname(seq),'processedAt':_rdate(),'cancelledAt':None,
             'displayFinancialStatus':'PAID','taxesIncluded':False,'currencyCode':'USD',
             'test':False,'tags':[],'paymentGatewayNames':['gift_card','shopify_payments'],
             'lineItems':[l],
             'shippingLines':[{'discountedPriceSet':{'shopMoney':{'amount':'0.00'}}}],
             'transactions':[gc_t,cc_t]}
    return {'order_seq':seq,'category':'split_tender','shopify_order_payload':order,
            'external_data':{'actual_3pl_shipping_invoice':float(sc)},'cogs_snapshot_table_entry':None}

def e_pos(seq,idx):
    p = random.choice(CATALOG); qty = random.randint(1,3)
    l,r,_,_ = _make_line(seq*100,p,qty=qty)
    gw = 'shopify_payments'; fee = _gw_fee(r,gw)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','pos_channel',tags=['pos'],
                 ext={'actual_3pl_shipping_invoice':0.0,'is_pos_order':True})

def e_bnd_zero(seq,idx):
    p = random.choice(CATALOG[:8]); gw = 'shopify_payments'; sc = _pick_ship(0)
    pr = p['price']; fee = _gw_fee(pr,gw)
    ec = _c(pr-sc-fee); ec = max(ec,Decimal('0.01'))
    l,r,_,_ = _make_line(seq*100,p,cogs_ov=ec)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','boundary_zero',
                 ext={'actual_3pl_shipping_invoice':float(sc)})

def e_bnd_neg(seq,idx):
    p = random.choice(CATALOG[:8]); gw = 'shopify_payments'; sc = _pick_ship(0)
    pr = p['price']; fee = _gw_fee(pr,gw)
    ec = _c(pr-sc-fee+Decimal('0.01')); ec = max(ec,Decimal('0.01'))
    l,r,_,_ = _make_line(seq*100,p,cogs_ov=ec)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','boundary_negative_cent',
                 ext={'actual_3pl_shipping_invoice':float(sc)})

def e_multiship(seq,idx):
    prods = random.sample(CATALOG,2); lines = []; tr = Decimal('0')
    for j,p in enumerate(prods):
        qty = random.randint(1,2); l,r,_,_ = _make_line(seq*100+j,p,qty=qty)
        lines.append(l); tr += r
    gw = _pick_gw(); fee = _gw_fee(tr,gw); sc = _pick_ship(2)
    return _wrap(seq,lines,gw,fee,Decimal('0'),'PAID','multiline_shipping',
                 ext={'actual_3pl_shipping_invoice':float(sc)})

def e_bundle(seq,idx):
    comps = [{'unit_cost':8.50,'qty':1},{'unit_cost':5.00,'qty':2}]
    p = random.choice(CATALOG[:8]); l,r,_,_ = _make_line(seq*100,p,bundle=comps)
    gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(1)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','bundle',
                 ext={'actual_3pl_shipping_invoice':float(sc)})

def e_hist(seq,idx):
    p = random.choice(CATALOG); lc = _c(p['price']*p['cogs_frac'])
    df = _rd(1.06,1.20); sc_cogs = _c(lc*df)
    l,r,_,_ = _make_line(seq*100,p); gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(1)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','historical_drift',
                 snap=float(sc_cogs), ext={'actual_3pl_shipping_invoice':float(sc)})

def e_tz(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p)
    gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(0)
    dt = datetime.datetime(2025,6,1,3,30,0) + datetime.timedelta(days=idx%300)
    at = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','timezone_rollup',at=at,
                 ext={'actual_3pl_shipping_invoice':float(sc),'shop_timezone':'America/New_York'})

def e_can_ship(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p,qty=2)
    gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(1); can = _rdate()
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','cancelled_partial_ship',cancelled=can,
                 ext={'actual_3pl_shipping_invoice':float(sc),'partial_fulfillment':True})

def e_promo(seq,idx):
    pp = random.choice(CATALOG[:8]); gp = random.choice(CATALOG[8:12])
    l1,r1,_,_ = _make_line(seq*100,pp)
    l2,_,_,_ = _make_line(seq*100+1,gp,cogs_ov=_c(gp['price']*gp['cogs_frac']))
    l2['discountedUnitPriceSet']['shopMoney']['amount'] = '0.00'
    gw = _pick_gw(); fee = _gw_fee(r1,gw); sc = _pick_ship(1)
    return _wrap(seq,[l1,l2],gw,fee,Decimal('0'),'PAID','promotional',
                 ext={'actual_3pl_shipping_invoice':float(sc),'promotional_gift':True})

def e_intl(seq,idx):
    p = random.choice(CATALOG); l,r,_,_ = _make_line(seq*100,p)
    gw = _pick_gw(); fee = _gw_fee(r,gw)
    sc = _pick_ship(3) + _rd(5.0,20.0); dest = random.choice(['CA','GB','AU'])
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','international_shipping',
                 ext={'actual_3pl_shipping_invoice':float(sc),'destination_country':dest})

def e_loss(seq,idx):
    p = CATALOG[15]; l,r,_,_ = _make_line(seq*100,p)
    gw = _pick_gw(); fee = _gw_fee(r,gw); sc = _pick_ship(2)
    return _wrap(seq,[l],gw,fee,Decimal('0'),'PAID','loss_leader',
                 ext={'actual_3pl_shipping_invoice':float(sc)})

BUILDERS = {
    'null_cogs':e_null_cogs,'shipping_lag':e_ship_lag,'gateway_fee_missing':e_gw_missing,
    'discount_code':e_disc_code,'stacked_discount':e_stacked,'sales_tax_embedded':e_tax,
    'partial_refund':e_part_ref,'full_refund_concession':e_full_conc,
    'full_refund_restocked':e_full_rest,'damaged_return':e_damaged,
    'split_tender':e_split,'pos_channel':e_pos,
    'boundary_zero':e_bnd_zero,'boundary_negative_cent':e_bnd_neg,
    'multiline_shipping':e_multiship,'bundle':e_bundle,
    'historical_drift':e_hist,'timezone_rollup':e_tz,
    'cancelled_partial_ship':e_can_ship,'promotional':e_promo,
    'international_shipping':e_intl,'loss_leader':e_loss,
}

def build_edges(start):
    orders = []; seq = start
    for cat,cnt in EDGE_DIST.items():
        for i in range(cnt):
            try:
                w = BUILDERS[cat](seq,i); w['category'] = cat; orders.append(w)
            except Exception as e:
                print('WARN cat=' + cat + ' i=' + str(i) + ': ' + str(e), file=sys.stderr)
            seq += 1
    return orders, seq

def compute_summary(all_orders):
    cat_counts = Counter(); total = len(all_orders)
    ev = 0; filt = 0; breach = 0; tl = Decimal('0'); tr_rev = Decimal('0')
    for w in all_orders:
        cat = w.get('category','?'); cat_counts[cat] += 1
        p = w['shopify_order_payload']
        fin = p.get('displayFinancialStatus','')
        is_t = p.get('test',False); can = p.get('cancelledAt')
        if fin in ('VOIDED','PENDING') or is_t or (can and cat.startswith('filtered')):
            filt += 1; continue
        if cat == 'null_cogs': continue
        ev += 1
        rev = Decimal('0')
        for li in p.get('lineItems',[]):
            amt = li.get('discountedUnitPriceSet',{}).get('shopMoney',{}).get('amount','0')
            qty = li.get('currentQuantity',1); rev += _c(Decimal(str(amt))*qty)
        tr_rev += rev
        cogs = Decimal('0'); skip = False
        for li in p.get('lineItems',[]):
            uc = li.get('variant',{}).get('inventoryItem',{}).get('unitCost')
            if uc is None: skip = True; break
            amt = (uc.get('amount') if isinstance(uc,dict) else uc)
            if amt is None: skip = True; break
            qty = li.get('currentQuantity',1); cogs += _c(Decimal(str(amt))*qty)
        if skip: continue
        ext = w.get('external_data',{}); sc = Decimal(str(ext.get('actual_3pl_shipping_invoice',0)))
        fee = Decimal('0')
        for txn in p.get('transactions',[]):
            for f in txn.get('fees',[]):
                fee += Decimal(str(f.get('amount',{}).get('amount','0')))
        if fee == Decimal('0') and cat != 'gateway_fee_missing':
            gw = p.get('paymentGatewayNames',['shopify_payments'])[0]
            fee = _gw_fee(rev,gw)
        gp = _c(rev - cogs - sc - fee)
        if gp < Decimal('0'): breach += 1; tl += abs(gp)
    br_rate = round(breach/ev*100,2) if ev else 0
    avg_loss = float(_c(tl/breach)) if breach else 0
    return {'total_orders':total,'baseline_normal':BASELINE_NORMAL,'baseline_filtered':BASELINE_FILTERED,
            'edge_cases':EDGE_CASE_ORDERS,'evaluable_orders':ev,'filtered_orders':filt,
            'breach_count':breach,'breach_rate_pct':br_rate,
            'total_revenue_usd':float(_c(tr_rev)),'total_f03_loss_usd':float(_c(tl)),
            'avg_loss_per_breach_usd':avg_loss,
            'category_distribution':dict(cat_counts),'edge_case_distribution':dict(EDGE_DIST),'seed':SEED}

def main():
    t0 = time.time(); all_orders = []; seq = 1
    print('[1/3] Baseline normal (' + str(BASELINE_NORMAL) + ')...')
    bl,seq,bst = build_baseline(seq); all_orders.extend(bl)
    print('      breach~' + str(bst['breach']) + '  full_ref=' + str(bst['full_ref']))
    print('[2/3] Filtered (' + str(BASELINE_FILTERED) + ')...')
    fl,seq = build_filtered(seq); all_orders.extend(fl)
    print('[3/3] Edge cases (' + str(EDGE_CASE_ORDERS) + ')...')
    el,seq = build_edges(seq); all_orders.extend(el)
    print('Shuffling...'); random.shuffle(all_orders)
    assert len(all_orders) == TARGET_TOTAL, 'Got ' + str(len(all_orders))
    print('Computing summary...'); s = compute_summary(all_orders)
    base = os.path.dirname(os.path.abspath(__file__))
    out_json = os.path.join(base,'large_fixtures.json')
    out_sum  = os.path.join(base,'large_fixtures_summary.json')
    print('Writing ' + out_json + ' ...')
    with open(out_json,'w',encoding='utf-8') as f: json.dump(all_orders,f)
    print('Writing ' + out_sum + ' ...')
    with open(out_sum,'w',encoding='utf-8') as f: json.dump(s,f,indent=2)
    elapsed = time.time()-t0
    print('DONE in ' + str(round(elapsed,1)) + 's')
    print('  Total: ' + str(s['total_orders']) + '  Evaluable: ' + str(s['evaluable_orders']))
    print('  Breach: ' + str(s['breach_count']) + ' (' + str(s['breach_rate_pct']) + '%)')
    print('  Loss: $' + str(s['total_f03_loss_usd']) + '  Revenue: $' + str(s['total_revenue_usd']))

main()
