// faqIndex.js
// ─────────────────────────────────────────────────────────────────────────────
// Sentinel Bank FAQ Semantic Index
// ─────────────────────────────────────────────────────────────────────────────
// Maps every possible user phrasing to the canonical FAQ question
// the RAG API expects. Each entry has:
//   canonical — the exact question string in FAQ-001.txt
//   signals   — keyword groups with weights (w). Score = sum of matched weights.
//
// Used by normalizeQuery() in ChatScreen.jsx:
//   score >= 5  → return canonical (confident match)
//   score < 5   → return raw query (let RAG handle it)
//
// To add a new FAQ question: append an entry following the same structure.
// ─────────────────────────────────────────────────────────────────────────────

export const FAQ_INDEX =
[
    // ── SECTION 1: TRANSFERS & PAYMENTS ──────────────────────────────────────
    {
      canonical: 'My transfer was debited but the receiver did not get the money.',
      signals: [
        { kw: ['debited','deducted','charged','taken'], w: 2 },
        { kw: ['not received','didn\'t receive','haven\'t received','not gotten','never got','not credited'], w: 4 },
        { kw: ['transfer','sent','payment','transaction'], w: 2 },
        { kw: ['receiver','recipient','beneficiary','other person','them','he','she'], w: 2 },
        { kw: ['but','however','yet','still'], w: 1 },
        { kw: ['money gone','balance reduced','money left','deducted from account'], w: 3 },
      ],
    },
    {
      canonical: 'I sent money to the wrong account. Can it be reversed?',
      signals: [
        { kw: ['wrong','incorrect','mistake','mistaken','error','accidentally','by accident'], w: 4 },
        { kw: ['account','number','person','recipient'], w: 2 },
        { kw: ['sent','transferred','paid','send'], w: 3 },
        { kw: ['reverse','reversal','recall','refund','get back','retrieve','undo'], w: 4 },
        { kw: ['wrong transfer','wrong account','wrong person','wrong number'], w: 5 },
      ],
    },
    {
      canonical: 'What are my daily transfer limits?',
      signals: [
        { kw: ['daily','day','per day'], w: 3 },
        { kw: ['limit','maximum','max','cap','restriction','how much'], w: 3 },
        { kw: ['transfer','send','payment','sending'], w: 2 },
        { kw: ['what is','what\'s','show me','tell me'], w: 1 },
        { kw: ['tier 1','tier 2','tier 3','kyc limit'], w: 4 },
        { kw: ['how much can i send','how much can i transfer'], w: 5 },
      ],
    },
    {
      canonical: 'How do I increase my transfer limit?',
      signals: [
        { kw: ['increase','raise','boost','expand','higher','upgrade','improve'], w: 4 },
        { kw: ['limit','maximum','cap'], w: 3 },
        { kw: ['transfer','sending','transaction'], w: 2 },
        { kw: ['want to send more','need to send more','can\'t send more'], w: 4 },
      ],
    },
    {
      canonical: 'My transfer is showing as pending. What does that mean?',
      signals: [
        { kw: ['pending','processing','on hold','not completed','in progress'], w: 5 },
        { kw: ['transfer','payment','transaction'], w: 2 },
        { kw: ['showing','shows','status','what does it mean','what is'], w: 2 },
        { kw: ['stuck','not moving','taking long','how long'], w: 3 },
      ],
    },
    {
      canonical: 'Can I schedule a future-dated transfer?',
      signals: [
        { kw: ['schedule','scheduled','future','later','tomorrow','next week','set up'], w: 5 },
        { kw: ['transfer','payment','send','recurring'], w: 2 },
        { kw: ['automatically','auto','automatic'], w: 2 },
        { kw: ['date','specific date','set date'], w: 3 },
        { kw: ['can i','is it possible','how do i'], w: 1 },
      ],
    },
    {
      canonical: 'What is Name Enquiry and why should I use it?',
      signals: [
        { kw: ['name enquiry','name verification','verify name','confirm name'], w: 6 },
        { kw: ['check name','see name','whose account','who owns'], w: 4 },
        { kw: ['before sending','before transfer'], w: 3 },
      ],
    },
    {
      canonical: 'My beneficiary says they haven\'t received payment after 24 hours.',
      signals: [
        { kw: ['24 hours','24hrs','one day','a day','yesterday','hours ago'], w: 4 },
        { kw: ['not received','haven\'t received','didn\'t get'], w: 4 },
        { kw: ['beneficiary','recipient','receiver','other person'], w: 3 },
        { kw: ['still waiting','still pending'], w: 3 },
      ],
    },
    {
      canonical: 'Why was my transfer returned/reversed?',
      signals: [
        { kw: ['returned','reversed','bounced','sent back','refunded'], w: 5 },
        { kw: ['transfer','payment','transaction'], w: 2 },
        { kw: ['why','reason','what happened'], w: 2 },
        { kw: ['automatically reversed','auto-reversed'], w: 4 },
      ],
    },
    {
      canonical: 'Can I transfer money to someone abroad?',
      signals: [
        { kw: ['abroad','international','overseas','foreign','outside nigeria','uk','usa','america','europe'], w: 5 },
        { kw: ['transfer','send money','wire','payment'], w: 3 },
        { kw: ['can i','how do i','is it possible'], w: 1 },
      ],
    },
    {
      canonical: 'What happens if I exceed my daily limit?',
      signals: [
        { kw: ['exceed','exceeded','over','above','past','gone over'], w: 4 },
        { kw: ['daily limit','limit','maximum'], w: 4 },
        { kw: ['what happens','what will','will i be'], w: 2 },
        { kw: ['limit exceeded','daily_transaction_limit_exceeded'], w: 6 },
      ],
    },
    {
      canonical: 'How do I add a new beneficiary?',
      signals: [
        { kw: ['add','save','create','new'], w: 3 },
        { kw: ['beneficiary','saved account','frequent recipient','contact','payee'], w: 5 },
        { kw: ['how do i','how to'], w: 1 },
      ],
    },
    {
      canonical: 'Is there a charge for transfers?',
      signals: [
        { kw: ['charge','fee','cost','price','how much','tariff','charges'], w: 4 },
        { kw: ['transfer','sending money','interbank','payment'], w: 3 },
        { kw: ['free','paid','deducted'], w: 2 },
        { kw: ['transfer fee','transfer charge'], w: 5 },
      ],
    },
    {
      canonical: 'What is NIBSS and how does it affect my transfer?',
      signals: [
        { kw: ['nibss','interbank','settlement system'], w: 6 },
        { kw: ['what is','explain','meaning'], w: 1 },
        { kw: ['affect','delay','maintenance'], w: 2 },
      ],
    },
    {
      canonical: 'My account was debited twice for one transaction.',
      signals: [
        { kw: ['twice','two times','double','2x','duplicate','charged twice','debited twice'], w: 6 },
        { kw: ['charged','debited','deducted'], w: 3 },
        { kw: ['same transaction','one payment','one transfer'], w: 3 },
      ],
    },

    // ── SECTION 2: CARD ISSUES ────────────────────────────────────────────────
    {
      canonical: 'Why was my card declined even though I have sufficient balance?',
      signals: [
        { kw: ['declined','declining','rejected','not working','failed','not accepted'], w: 4 },
        { kw: ['card','debit card'], w: 3 },
        { kw: ['balance','money','funds','sufficient','enough'], w: 3 },
        { kw: ['have money','have balance','but i have'], w: 4 },
        { kw: ['why','reason','keeps','keeps declining'], w: 2 },
      ],
    },
    {
      canonical: 'My card got stolen. How do I block it immediately?',
      signals: [
        { kw: ['stolen','theft','rob','robbed','someone took','missing','lost'], w: 5 },
        { kw: ['card'], w: 3 },
        { kw: ['block','freeze','stop','disable','cancel'], w: 4 },
        { kw: ['immediately','now','urgent','quickly','asap','right away'], w: 3 },
        { kw: ['want to block','need to block','block my card','i want to block'], w: 6 },
      ],
    },
    {
      canonical: 'I lost my card. What should I do?',
      signals: [
        { kw: ['lost','misplaced','can\'t find','cannot find','missing'], w: 5 },
        { kw: ['card','debit card'], w: 4 },
        { kw: ['what should i do','what do i do','help','how do i'], w: 2 },
      ],
    },
    {
      canonical: 'How do I block my card temporarily?',
      signals: [
        { kw: ['temporarily','temporarily block','for now','short time','temp','pause'], w: 5 },
        { kw: ['block','freeze','disable','stop','suspend'], w: 4 },
        { kw: ['card'], w: 3 },
        { kw: ['not permanently','not forever'], w: 3 },
      ],
    },
    {
      canonical: 'The ATM did not dispense cash but my account was debited.',
      signals: [
        { kw: ['atm','cash machine','pos machine','withdrawal machine'], w: 4 },
        { kw: ['no cash','didn\'t dispense','cash not given','no money came out','machine didn\'t give'], w: 5 },
        { kw: ['debited','charged','deducted','taken','money gone'], w: 4 },
        { kw: ['atm debit but no cash','atm took money'], w: 6 },
      ],
    },
    {
      canonical: 'How do I request a new debit card?',
      signals: [
        { kw: ['request','order','get','apply for','need'], w: 3 },
        { kw: ['new card','debit card','replacement card','fresh card'], w: 5 },
        { kw: ['how do i','how to','where to'], w: 2 },
        { kw: ['card delivery','card pickup'], w: 3 },
      ],
    },
    {
      canonical: 'How do I change my card PIN?',
      signals: [
        { kw: ['change','reset','update','new','modify'], w: 3 },
        { kw: ['card pin','atm pin','pin'], w: 5 },
        { kw: ['forgot my pin','can\'t remember pin'], w: 4 },
        { kw: ['how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'My card is expiring soon. What should I do?',
      signals: [
        { kw: ['expir','expire','expiry','expiration','about to expire','expiring soon'], w: 6 },
        { kw: ['card'], w: 3 },
        { kw: ['renew','renewal','new card','replace'], w: 3 },
        { kw: ['what should i do','what do i do'], w: 2 },
      ],
    },
    {
      canonical: 'Can I use my Sentinel Bank card abroad?',
      signals: [
        { kw: ['abroad','international','overseas','foreign country','travel','outside nigeria'], w: 5 },
        { kw: ['use my card','card work','card abroad'], w: 4 },
        { kw: ['can i','does my card'], w: 2 },
      ],
    },
    {
      canonical: 'What is a virtual card and how do I get one?',
      signals: [
        { kw: ['virtual card','virtual debit','digital card'], w: 6 },
        { kw: ['what is','how do i get','how to get'], w: 2 },
        { kw: ['online payment','international site','amazon','netflix','online shopping'], w: 2 },
      ],
    },
    {
      canonical: 'Why is my card not working on international websites?',
      signals: [
        { kw: ['international website','foreign website','online shopping','amazon','netflix','paypal','international payment'], w: 5 },
        { kw: ['not working','declining','rejected','failed','doesn\'t work'], w: 4 },
        { kw: ['card','debit card'], w: 2 },
      ],
    },

    // ── SECTION 3: ACCOUNT MANAGEMENT & KYC ──────────────────────────────────
    {
      canonical: 'How do I open a Sentinel Bank account?',
      signals: [
        { kw: ['open','create','new account','register','sign up','start'], w: 4 },
        { kw: ['account','sentinel account','bank account'], w: 3 },
        { kw: ['how do i','how to','steps to'], w: 2 },
        { kw: ['open an account','open account'], w: 5 },
      ],
    },
    {
      canonical: 'How do I upgrade my account tier?',
      signals: [
        { kw: ['upgrade','tier upgrade','move to tier','go to tier','promote','increase tier'], w: 5 },
        { kw: ['account','tier','level','kyc'], w: 3 },
        { kw: ['how do i','how to','steps'], w: 2 },
        { kw: ['tier 1 to tier 2','tier 2 to tier 3','basic to premium'], w: 6 },
        { kw: ['upgrade my account','want to upgrade'], w: 5 },
      ],
    },
    {
      canonical: 'How do I link my BVN to my account?',
      signals: [
        { kw: ['bvn','bank verification number'], w: 6 },
        { kw: ['link','connect','add','attach','verify'], w: 3 },
        { kw: ['how do i','how to'], w: 2 },
        { kw: ['link bvn','add bvn'], w: 5 },
      ],
    },
    {
      canonical: 'How do I update my phone number on my account?',
      signals: [
        { kw: ['phone number','mobile number','number','contact number'], w: 4 },
        { kw: ['update','change','edit','modify','new number'], w: 4 },
        { kw: ['account','registered number'], w: 2 },
        { kw: ['how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'How do I update my email address?',
      signals: [
        { kw: ['email','email address','mail'], w: 5 },
        { kw: ['update','change','edit','modify','new email'], w: 4 },
        { kw: ['how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'How do I change my account name?',
      signals: [
        { kw: ['account name','name change','change name','update name'], w: 6 },
        { kw: ['married','marriage','maiden name','new name'], w: 4 },
        { kw: ['how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'How do I close my Sentinel Bank account?',
      signals: [
        { kw: ['close','close account','shut down','terminate','deactivate'], w: 6 },
        { kw: ['account'], w: 2 },
        { kw: ['how do i','how to','want to close'], w: 2 },
      ],
    },
    {
      canonical: 'Can I have more than one account?',
      signals: [
        { kw: ['more than one','multiple accounts','two accounts','second account','another account'], w: 6 },
        { kw: ['can i','is it possible','allowed'], w: 2 },
      ],
    },
    {
      canonical: 'What is a Solo account?',
      signals: [
        { kw: ['solo account','solo','goal account','goal savings'], w: 6 },
        { kw: ['what is','explain','tell me about'], w: 2 },
      ],
    },
    {
      canonical: 'How long does it take to verify my account?',
      signals: [
        { kw: ['verify','verification','activate','activation'], w: 4 },
        { kw: ['how long','how many days','time','duration'], w: 4 },
        { kw: ['account'], w: 2 },
        { kw: ['when will my account be ready','when can i use my account'], w: 5 },
      ],
    },
    {
      canonical: 'I forgot my account number. How do I find it?',
      signals: [
        { kw: ['forgot','can\'t remember','don\'t know','find','locate'], w: 4 },
        { kw: ['account number','nuban','acct number'], w: 5 },
        { kw: ['where is','where can i find','how do i find'], w: 3 },
      ],
    },

    // ── SECTION 4: MOBILE APP & DIGITAL BANKING ───────────────────────────────
    {
      canonical: 'I cannot log into the mobile app.',
      signals: [
        { kw: ['can\'t login','cannot login','can\'t log in','cannot log in','login problem','not logging in'], w: 6 },
        { kw: ['app','mobile app','application'], w: 3 },
        { kw: ['access','enter','get in','open'], w: 2 },
        { kw: ['locked out','locked','suspended','blocked account'], w: 4 },
      ],
    },
    {
      canonical: 'I am not receiving OTPs.',
      signals: [
        { kw: ['otp','one time password','verification code','code','sms code'], w: 5 },
        { kw: ['not receiving','not getting','didn\'t get','not coming','no otp','otp not sent'], w: 5 },
        { kw: ['phone','sms','message'], w: 2 },
      ],
    },
    {
      canonical: 'How do I reset my app password?',
      signals: [
        { kw: ['reset','forgot','recover','change'], w: 4 },
        { kw: ['password','passcode','pin'], w: 4 },
        { kw: ['app','login','account'], w: 2 },
        { kw: ['forgot password','reset password','can\'t remember password'], w: 5 },
      ],
    },
    {
      canonical: 'How do I set up biometric login (fingerprint/face ID)?',
      signals: [
        { kw: ['biometric','fingerprint','face id','face recognition','touch id'], w: 6 },
        { kw: ['set up','enable','activate','turn on','how to'], w: 3 },
        { kw: ['login','log in'], w: 2 },
      ],
    },
    {
      canonical: 'The app keeps crashing. What should I do?',
      signals: [
        { kw: ['crash','crashing','keeps crashing','closes','shutting down','force close','not opening','freezing'], w: 6 },
        { kw: ['app','mobile app','application'], w: 3 },
        { kw: ['what should i do','how to fix','fix'], w: 2 },
      ],
    },
    {
      canonical: 'How do I enable transaction notifications?',
      signals: [
        { kw: ['notification','alert','sms alert','push notification','transaction alert'], w: 5 },
        { kw: ['enable','turn on','activate','set up'], w: 3 },
        { kw: ['how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'I accidentally deleted the app. Will I lose my data?',
      signals: [
        { kw: ['deleted','uninstalled','removed','lost the app'], w: 5 },
        { kw: ['app','application'], w: 2 },
        { kw: ['data','account','information','history','saved'], w: 3 },
        { kw: ['will i lose','lose my data','lose my account'], w: 4 },
      ],
    },
    {
      canonical: 'How do I use USSD banking?',
      signals: [
        { kw: ['ussd','*737#','ussd code','dial code'], w: 6 },
        { kw: ['how to','how do i','use','bank without internet'], w: 2 },
        { kw: ['no internet','offline banking','without data'], w: 3 },
      ],
    },
    {
      canonical: 'Is internet banking available?',
      signals: [
        { kw: ['internet banking','web banking','online banking','browser banking','website banking'], w: 6 },
        { kw: ['available','access','use'], w: 2 },
        { kw: ['is there','do you have','can i use'], w: 2 },
      ],
    },
    {
      canonical: 'How do I transfer between my own Sentinel accounts?',
      signals: [
        { kw: ['own account','my accounts','between accounts','account to account','self transfer'], w: 5 },
        { kw: ['transfer','move money','send'], w: 3 },
        { kw: ['savings to current','current to savings'], w: 4 },
      ],
    },

    // ── SECTION 5: ACCOUNT SERVICES & CHARGES ────────────────────────────────
    {
      canonical: 'How do I request a bank statement?',
      signals: [
        { kw: ['bank statement','statement','account statement','transaction history download'], w: 5 },
        { kw: ['request','get','download','print','generate'], w: 3 },
        { kw: ['how do i','how to'], w: 2 },
        { kw: ['pdf statement','email statement'], w: 4 },
      ],
    },
    {
      canonical: 'Why am I being charged monthly fees?',
      signals: [
        { kw: ['monthly fee','maintenance fee','monthly charge','account fee','charged every month'], w: 6 },
        { kw: ['why','reason','what is'], w: 2 },
        { kw: ['deducted monthly','monthly deduction'], w: 4 },
      ],
    },
    {
      canonical: 'What is the VAT on banking transactions?',
      signals: [
        { kw: ['vat','value added tax','tax on transactions','banking tax'], w: 6 },
        { kw: ['what is','how much','percentage'], w: 2 },
      ],
    },
    {
      canonical: 'How do I dispute an unknown charge on my account?',
      signals: [
        { kw: ['dispute','unknown charge','strange deduction','unauthorized charge','unexplained charge'], w: 6 },
        { kw: ['charge','deduction','debit','fee'], w: 3 },
        { kw: ['how do i','how to'], w: 2 },
        { kw: ['i didn\'t authorise','i didn\'t do','i didn\'t approve'], w: 4 },
      ],
    },
    {
      canonical: 'What is the minimum balance for my account?',
      signals: [
        { kw: ['minimum balance','minimum amount','least amount','lowest balance'], w: 6 },
        { kw: ['account','savings','current'], w: 2 },
        { kw: ['what is','how much'], w: 2 },
      ],
    },
    {
      canonical: 'How do I set up a standing order (recurring transfer)?',
      signals: [
        { kw: ['standing order','recurring transfer','automatic transfer','scheduled transfer','repeat transfer','auto debit'], w: 6 },
        { kw: ['how do i','how to','set up','create'], w: 2 },
      ],
    },
    {
      canonical: 'How do I get a reference letter from my bank?',
      signals: [
        { kw: ['reference letter','bank reference','confirmation letter','bank letter','letter from bank'], w: 6 },
        { kw: ['how do i','how to','get','request'], w: 2 },
      ],
    },
    {
      canonical: 'Can I receive salary into my Sentinel Bank account?',
      signals: [
        { kw: ['salary','wages','pay','payroll'], w: 4 },
        { kw: ['receive','credit','into my account','sent to'], w: 3 },
        { kw: ['can i','is it possible','employer'], w: 2 },
        { kw: ['sort code','account number for salary'], w: 4 },
      ],
    },

    // ── SECTION 6: LOANS & CREDIT ─────────────────────────────────────────────
    {
      canonical: 'What loan products does Sentinel Bank offer?',
      signals: [
        { kw: ['loan products','types of loan','loans available','what loans','loan options'], w: 5 },
        { kw: ['loan','borrow','credit'], w: 3 },
        { kw: ['what','types','available'], w: 2 },
        { kw: ['personal loan','asset finance','salary advance','overdraft'], w: 2 },
      ],
    },
    {
      canonical: 'How do I apply for an instant salary advance?',
      signals: [
        { kw: ['salary advance','advance salary','advance on salary'], w: 6 },
        { kw: ['apply','get','how to'], w: 2 },
        { kw: ['instant loan','quick loan','fast loan'], w: 2 },
      ],
    },
    {
      canonical: 'What is the interest rate on Sentinel Bank loans?',
      signals: [
        { kw: ['interest rate','rate','percentage','how much interest'], w: 5 },
        { kw: ['loan','borrow','credit'], w: 3 },
        { kw: ['what is','how much','tell me'], w: 2 },
      ],
    },
    {
      canonical: 'How do I check my loan repayment schedule?',
      signals: [
        { kw: ['repayment schedule','payment schedule','loan schedule','amortisation'], w: 6 },
        { kw: ['check','see','view','find'], w: 2 },
        { kw: ['loan'], w: 2 },
      ],
    },
    {
      canonical: 'What happens if I miss a loan repayment?',
      signals: [
        { kw: ['miss','missed','late payment','default','didn\'t pay','can\'t pay'], w: 5 },
        { kw: ['loan','repayment','installment'], w: 3 },
        { kw: ['what happens','consequence','penalty'], w: 3 },
      ],
    },
    {
      canonical: 'Can I pay off my loan early?',
      signals: [
        { kw: ['early repayment','pay off early','clear loan early','settle loan','pay before due'], w: 6 },
        { kw: ['loan','outstanding'], w: 2 },
        { kw: ['can i','is it possible','penalty'], w: 2 },
      ],
    },
    {
      canonical: 'How long does loan approval take?',
      signals: [
        { kw: ['loan approval','how long','time','duration','when','days'], w: 4 },
        { kw: ['loan','application'], w: 3 },
        { kw: ['approve','disbursed','processing time'], w: 4 },
      ],
    },

    // ── SECTION 7: SAVINGS & INVESTMENTS ──────────────────────────────────────
    {
      canonical: 'What savings accounts does Sentinel Bank offer?',
      signals: [
        { kw: ['savings account','types of savings','savings products','savings options'], w: 5 },
        { kw: ['what','available','offer','types'], w: 2 },
        { kw: ['basic savings','premium savings','solo','fixed deposit'], w: 3 },
      ],
    },
    {
      canonical: 'How does interest work on my savings account?',
      signals: [
        { kw: ['interest','interest rate','earn interest','how much interest'], w: 4 },
        { kw: ['savings','savings account'], w: 3 },
        { kw: ['how does','how is','how do i earn','calculated','when is it paid'], w: 3 },
      ],
    },
    {
      canonical: 'How do I open a fixed deposit?',
      signals: [
        { kw: ['fixed deposit','fix deposit','fixed term','term deposit'], w: 6 },
        { kw: ['open','create','start','how do i'], w: 3 },
        { kw: ['high interest','13%','earn more'], w: 2 },
      ],
    },
    {
      canonical: 'What happens to my fixed deposit at maturity?',
      signals: [
        { kw: ['fixed deposit','fix deposit'], w: 4 },
        { kw: ['maturity','matures','expires','end of term'], w: 5 },
        { kw: ['what happens','auto renew','renew'], w: 3 },
      ],
    },
    {
      canonical: 'Can I withdraw from my Solo account before the target date?',
      signals: [
        { kw: ['solo account','solo'], w: 4 },
        { kw: ['withdraw','withdrawal','take out','before target','before date','break'], w: 5 },
        { kw: ['can i','is it possible','penalty'], w: 2 },
      ],
    },
    {
      canonical: 'What is the Virtual Dollar Card and how do I use it?',
      signals: [
        { kw: ['virtual dollar card','dollar card','usd card','dollar virtual'], w: 6 },
        { kw: ['what is','how do i use','how to use'], w: 2 },
        { kw: ['amazon','netflix','international site','foreign website'], w: 2 },
      ],
    },

    // ── SECTION 8: FRAUD & SECURITY ───────────────────────────────────────────
    {
      canonical: 'Someone called asking for my PIN and OTP. What should I do?',
      signals: [
        { kw: ['called me','phone call','someone called','stranger called','person called'], w: 5 },
        { kw: ['pin','otp','password','details','account info'], w: 4 },
        { kw: ['asking for','requested','wants','demand'], w: 4 },
        { kw: ['scam call','fraud call'], w: 5 },
      ],
    },
    {
      canonical: 'I noticed an unauthorised transaction on my account.',
      signals: [
        { kw: ['unauthorised','unauthorized','strange transaction','unknown transaction','transaction i didn\'t do','didn\'t make this'], w: 6 },
        { kw: ['transaction','charge','debit','deduction'], w: 3 },
        { kw: ['noticed','saw','found'], w: 2 },
        { kw: ['someone used my account','someone made a transaction'], w: 5 },
      ],
    },
    {
      canonical: 'What is phishing and how do I protect myself?',
      signals: [
        { kw: ['phishing','fake link','fake website','fake sms','impersonation'], w: 6 },
        { kw: ['protect','protection','safe','secure'], w: 3 },
        { kw: ['what is','explain'], w: 2 },
      ],
    },
    {
      canonical: 'How do I secure my Sentinel Bank account?',
      signals: [
        { kw: ['secure','security','protect','safety','safe'], w: 4 },
        { kw: ['account','my account'], w: 2 },
        { kw: ['how do i','tips','best practices','advice'], w: 3 },
        { kw: ['account security','keep account safe'], w: 5 },
      ],
    },
    {
      canonical: 'I think my account has been hacked.',
      signals: [
        { kw: ['hacked','compromised','breached','someone accessed','unauthorised access','account broken into'], w: 6 },
        { kw: ['think','believe','suspect','i feel'], w: 2 },
        { kw: ['account'], w: 2 },
        { kw: ['my account was hacked','account has been hacked'], w: 6 },
      ],
    },
    {
      canonical: 'What is two-factor authentication (2FA) and how do I enable it?',
      signals: [
        { kw: ['two factor','2fa','two-factor','double verification','extra security','second verification'], w: 6 },
        { kw: ['what is','enable','set up','turn on'], w: 2 },
      ],
    },

    // ── SECTION 9: BILL PAYMENTS & AIRTIME ────────────────────────────────────
    {
      canonical: 'How do I pay bills (electricity, DSTV, water) on the app?',
      signals: [
        { kw: ['electricity','nepa','phcn','dstv','gotv','water bill','cable tv','bill payment'], w: 5 },
        { kw: ['pay','payment','how do i'], w: 2 },
        { kw: ['app','online','ussd'], w: 2 },
      ],
    },
    {
      canonical: 'How do I buy airtime or data on the app?',
      signals: [
        { kw: ['airtime','recharge','data','mtn','airtel','glo','9mobile','etisalat'], w: 5 },
        { kw: ['buy','purchase','top up','how do i'], w: 3 },
        { kw: ['app','phone','online'], w: 2 },
      ],
    },
    {
      canonical: 'How do I pay school fees through the app?',
      signals: [
        { kw: ['school fees','school payment','tuition','university fees','education payment'], w: 6 },
        { kw: ['pay','how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'Can I pay taxes using Sentinel Bank?',
      signals: [
        { kw: ['tax','taxes','firs','lirs','remita','government payment'], w: 6 },
        { kw: ['pay','payment','can i'], w: 2 },
      ],
    },

    // ── SECTION 10: COMPLAINTS & ESCALATIONS ──────────────────────────────────
    {
      canonical: 'How do I file a formal complaint?',
      signals: [
        { kw: ['complain','complaint','formal complaint','lodge complaint','report issue'], w: 5 },
        { kw: ['how do i','how to','where to'], w: 2 },
        { kw: ['file','submit','make','raise'], w: 3 },
      ],
    },
    {
      canonical: 'What is the complaint resolution timeline?',
      signals: [
        { kw: ['complaint','resolution','how long','timeline','sla'], w: 4 },
        { kw: ['how long will it take','when will it be resolved','time to resolve'], w: 5 },
        { kw: ['resolve','fix','sort out'], w: 2 },
      ],
    },
    {
      canonical: 'Can I escalate to the CBN if Sentinel Bank does not resolve my complaint?',
      signals: [
        { kw: ['cbn','central bank','escalate','escalation'], w: 6 },
        { kw: ['not resolved','not fixed','still pending','no response'], w: 4 },
        { kw: ['can i go to cbn','report to cbn'], w: 5 },
      ],
    },
    {
      canonical: 'How do I get a complaint reference number?',
      signals: [
        { kw: ['complaint reference','reference number','ticket number','case number'], w: 6 },
        { kw: ['how do i get','where is','find'], w: 2 },
      ],
    },

    // ── SECTION 11: CONTACT & BRANCH ──────────────────────────────────────────
    {
      canonical: 'What are Sentinel Bank\'s contact details?',
      signals: [
        { kw: ['contact','phone number','call centre','how to reach','contact details'], w: 5 },
        { kw: ['sentinel bank','customer care','support number'], w: 3 },
        { kw: ['email','hotline','address'], w: 2 },
      ],
    },
    {
      canonical: 'How do I find the nearest Sentinel Bank branch or ATM?',
      signals: [
        { kw: ['nearest branch','nearest atm','branch locator','atm locator','find branch','find atm'], w: 6 },
        { kw: ['close to me','near me','location','nearby'], w: 4 },
      ],
    },
    {
      canonical: 'How do I contact Sentinel Bank on social media?',
      signals: [
        { kw: ['social media','twitter','instagram','facebook','linkedin','x.com'], w: 6 },
        { kw: ['contact','reach','dm','message'], w: 2 },
      ],
    },
    {
      canonical: 'What do I do if I have an emergency outside banking hours?',
      signals: [
        { kw: ['emergency','outside hours','after hours','weekend','night','closed','after banking hours'], w: 5 },
        { kw: ['what do i do','who do i call','help'], w: 3 },
      ],
    },

    // ── SECTION 12: MISCELLANEOUS ─────────────────────────────────────────────
    {
      canonical: 'How do I refer a friend to Sentinel Bank?',
      signals: [
        { kw: ['refer','referral','refer a friend','referral bonus','invite'], w: 6 },
        { kw: ['how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'Does Sentinel Bank offer business accounts?',
      signals: [
        { kw: ['business account','corporate account','company account','sme','enterprise'], w: 5 },
        { kw: ['do you offer','is there','available'], w: 2 },
      ],
    },
    {
      canonical: 'How do I apply for a POS terminal for my business?',
      signals: [
        { kw: ['pos terminal','pos machine','point of sale','pos device'], w: 6 },
        { kw: ['apply','get','request','how to'], w: 2 },
        { kw: ['business','merchant','shop'], w: 2 },
      ],
    },
    {
      canonical: 'What is Sentinel Bank\'s privacy policy on my data?',
      signals: [
        { kw: ['privacy','data privacy','my data','personal data','ndpr'], w: 6 },
        { kw: ['policy','what do you do with','use my data'], w: 3 },
      ],
    },
    {
      canonical: 'How do I check my account balance?',
      signals: [
        { kw: ['check balance','see balance','view balance','account balance','current balance'], w: 6 },
        { kw: ['how do i','how to','ussd balance'], w: 2 },
        { kw: ['*737*1#','ussd'], w: 3 },
      ],
    },
    {
      canonical: 'Can I operate my account via WhatsApp?',
      signals: [
        { kw: ['whatsapp','whatsapp banking','via whatsapp'], w: 6 },
        { kw: ['can i','is it possible','use'], w: 2 },
      ],
    },
    {
      canonical: 'What is BVN and why do I need it?',
      signals: [
        { kw: ['bvn','bank verification number'], w: 5 },
        { kw: ['what is','why do i need','explain','meaning'], w: 3 },
      ],
    },
    {
      canonical: 'What is NIN and why do I need it for banking?',
      signals: [
        { kw: ['nin','national identification number','national identity'], w: 5 },
        { kw: ['what is','why do i need','explain','banking','link'], w: 3 },
      ],
    },
    {
      canonical: 'How do I report a Sentinel Bank staff for misconduct?',
      signals: [
        { kw: ['staff','employee','worker','banker','agent'], w: 4 },
        { kw: ['misconduct','misbehave','rude','fraud','corrupt','unprofessional'], w: 5 },
        { kw: ['report','complain about'], w: 3 },
      ],
    },
    {
      canonical: 'What is NUBAN and why does it matter?',
      signals: [
        { kw: ['nuban','nigeria uniform bank account number','account number format','10 digit'], w: 6 },
        { kw: ['what is','explain','meaning'], w: 2 },
      ],
    },
    {
      canonical: 'How do I enable or disable transaction alerts?',
      signals: [
        { kw: ['transaction alert','sms alert','push notification','debit alert'], w: 4 },
        { kw: ['enable','disable','turn on','turn off','stop','activate'], w: 4 },
        { kw: ['how do i','how to'], w: 2 },
      ],
    },

    // ── SECTION 13: ADDITIONAL ────────────────────────────────────────────────
    {
      canonical: 'How do I print my account details?',
      signals: [
        { kw: ['print','printout','account details','account information sheet'], w: 5 },
        { kw: ['how do i','how to','get a copy'], w: 2 },
      ],
    },
    {
      canonical: 'Is my money safe with Sentinel Bank?',
      signals: [
        { kw: ['safe','secure','ndic','insured','guaranteed','reliable'], w: 5 },
        { kw: ['my money','deposit','funds'], w: 3 },
        { kw: ['is my money safe','are my funds safe'], w: 6 },
      ],
    },
    {
      canonical: 'How do I reactivate a dormant account?',
      signals: [
        { kw: ['dormant','inactive','reactivate','re-activate','activate account'], w: 6 },
        { kw: ['how do i','how to'], w: 2 },
        { kw: ['account been inactive','not used account'], w: 4 },
      ],
    },
    {
      canonical: 'How do I get a Sentinel Bank debit card for the first time?',
      signals: [
        { kw: ['first time','first card','i don\'t have a card','no card yet','how do i get a card'], w: 5 },
        { kw: ['debit card','card'], w: 3 },
        { kw: ['how do i','how to','get'], w: 2 },
      ],
    },
    {
      canonical: 'What should I do if my card is about to expire?',
      signals: [
        { kw: ['card expiry','card expiring','expire soon','expiry date','renew card'], w: 6 },
        { kw: ['what should i do','what do i do'], w: 2 },
      ],
    },
    {
      canonical: 'Can I have a joint account with Sentinel Bank?',
      signals: [
        { kw: ['joint account','shared account','two names','dual signatories'], w: 6 },
        { kw: ['can i','is it possible','open'], w: 2 },
      ],
    },
    {
      canonical: 'How do I set a transaction PIN for the app?',
      signals: [
        { kw: ['transaction pin','app pin','set pin','4 digit pin','payment pin'], w: 6 },
        { kw: ['how do i','how to','set','change'], w: 2 },
      ],
    },
    {
      canonical: 'How do I view my full transaction history?',
      signals: [
        { kw: ['transaction history','all transactions','full history','past transactions','view transactions'], w: 6 },
        { kw: ['how do i','how to','view','see'], w: 2 },
        { kw: ['statement','history','records'], w: 2 },
      ],
    },
    {
      canonical: 'What is a chargeback and how do I request one?',
      signals: [
        { kw: ['chargeback','charge back','dispute transaction','merchant dispute','goods not received'], w: 6 },
        { kw: ['what is','how do i','request'], w: 2 },
      ],
    },
    {
      canonical: 'How do I apply for overdraft protection?',
      signals: [
        { kw: ['overdraft','overdraft facility','overdraft protection'], w: 6 },
        { kw: ['apply','get','how do i','request'], w: 2 },
      ],
    },
    {
      canonical: 'My salary was not credited on the expected date.',
      signals: [
        { kw: ['salary','wages','pay','payroll'], w: 4 },
        { kw: ['not credited','not received','didn\'t come','not paid','delayed'], w: 5 },
        { kw: ['expected date','payday','salary day'], w: 4 },
      ],
    },
    {
      canonical: 'What currencies can I hold in my Sentinel Bank account?',
      signals: [
        { kw: ['currency','currencies','foreign currency','usd','eur','gbp','dollar','euro','pound'], w: 5 },
        { kw: ['hold','keep','store','account'], w: 3 },
        { kw: ['what currencies','which currencies'], w: 4 },
      ],
    },
    {
      canonical: 'How do I open a domiciliary account?',
      signals: [
        { kw: ['domiciliary','dom account','foreign currency account','dollar account','euro account'], w: 6 },
        { kw: ['open','how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'Can I send money to a domiciliary account from Naira?',
      signals: [
        { kw: ['domiciliary','dom account','foreign account'], w: 4 },
        { kw: ['naira','ngn','from naira'], w: 4 },
        { kw: ['fund','transfer','send','convert'], w: 3 },
      ],
    },
    {
      canonical: 'How do I apply for a Sentinel Bank mortgage?',
      signals: [
        { kw: ['mortgage','home loan','property loan','house loan'], w: 6 },
        { kw: ['apply','how do i','how to'], w: 2 },
      ],
    },
    {
      canonical: 'What is the CBN and how does it relate to Sentinel Bank?',
      signals: [
        { kw: ['cbn','central bank of nigeria'], w: 5 },
        { kw: ['what is','explain','who is','relationship'], w: 3 },
      ],
    },
    {
      canonical: 'How does the fraud detection system work?',
      signals: [
        { kw: ['fraud detection','fraud system','anti-fraud','how fraud is detected'], w: 6 },
        { kw: ['how does','explain','tell me about'], w: 2 },
      ],
    },
    {
      canonical: 'How do I earn more interest on my savings?',
      signals: [
        { kw: ['earn more interest','more interest','higher interest','maximize savings','grow savings'], w: 6 },
        { kw: ['savings','money','deposit'], w: 2 },
        { kw: ['how do i','how to','tips'], w: 2 },
      ],
    },
    {
      canonical: 'Is Sentinel Bank available outside Nigeria?',
      signals: [
        { kw: ['outside nigeria','international','abroad','foreign country','another country'], w: 5 },
        { kw: ['available','access','use','open account'], w: 3 },
        { kw: ['is sentinel bank available'], w: 5 },
      ],
    },
    {
      canonical: 'How do I opt out of marketing communications?',
      signals: [
        { kw: ['marketing','promotional','advertisements','promo messages','spam','unsubscribe'], w: 6 },
        { kw: ['opt out','stop','disable','remove','unsubscribe'], w: 4 },
      ],
    },
];